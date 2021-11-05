import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askokcancel, showerror, showinfo, showwarning
from tkinter.filedialog import asksaveasfilename
import ui.label as lb
import ui.constraints as const
import queue
import os

class UI_file_explorer(tk.Toplevel):
    def __init__(self, parent, socket_queue, ui_queues):
        super().__init__(parent)
        self.ui_queue = queue.Queue()
        self.socket_queue = socket_queue
        self.ui_queues = ui_queues
        ui_queues['file'] = self.ui_queue

        self.title = lb.FILE_EXPLORER_TITLE
        self.resizable(False, False)
        self['padx'] = const.WINDOW_BORDER_PADDING
        self['pady'] = const.WINDOW_BORDER_PADDING

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=30)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)

        self.btn_up = tk.Button(self, text = lb.FILE_EXP_UP, width = 10, command = self.up_folder)
        self.btn_up.grid(row = 0, column = 0, sticky = tk.W)

        self.txt_path_input = tk.Entry(self)
        self.txt_path_input.grid(row = 0, column = 1, sticky = tk.EW)
        self.txt_path_input['state'] = 'readonly'

        # create a treeview
        columns = ('#1', '#2', '#3', '#4')
        self.trv_file_exp = ttk.Treeview(self, columns = columns, show = 'headings', height = 20)

        # config columns width
        self.trv_file_exp.column('#1',minwidth = 50, width = 300, anchor = tk.W)
        self.trv_file_exp.column('#2',minwidth = 50, width = 200, anchor = tk.W)
        self.trv_file_exp.column('#3',minwidth = 50, width = 200, anchor = tk.W)
        self.trv_file_exp.column('#4',minwidth = 50, width = 100, anchor = tk.E)

        # define headings
        self.trv_file_exp.heading('#1', text = lb.FILE_EXP_TRV_NAME)
        self.trv_file_exp.heading('#2', text = lb.FILE_EXP_TRV_DATEMOD)
        self.trv_file_exp.heading('#3', text = lb.FILE_EXP_TRV_TYPE)
        self.trv_file_exp.heading('#4', text = lb.FILE_EXP_TRV_SIZE)

        self.trv_file_exp.grid(row = 1, column = 0, columnspan = 4, pady = (5,0), sticky = tk.NSEW)

        # add a scrollbar
        self.scrollbar = ttk.Scrollbar(self, orient = tk.VERTICAL, command = self.trv_file_exp.yview)
        self.trv_file_exp.configure(yscroll = self.scrollbar.set)
        self.scrollbar.grid(row = 1, column = 4, pady = (5,0), sticky = 'ns')

        self.trv_file_exp.bind("<Double-Button-1>", self.choose_in_tree)  

        self.btn_copy_stt = tk.StringVar(self, lb.FILE_EXP_COPY)
        self.btn_copy = tk.Button(self, textvariable = self.btn_copy_stt, width = 8, command = self.copy_file)
        self.btn_copy.grid(row = 0, column = 2, sticky = tk.E)

        self.btn_delete_stt = tk.StringVar(self, lb.FILE_EXP_DELETE)
        self.btn_delete = tk.Button(self, textvariable = self.btn_delete_stt, width = 8, command = self.delete_file)
        self.btn_delete.grid(row = 0, column = 3, sticky=tk.E)

        self.goto_dir("")
        self.after(const.UPDATE_TIME, self.periodic_call)

    def up_folder(self):
        dir = self.txt_path_input.get()
        if dir != lb.WAIT:
            parent_dir = os.path.dirname(dir)
            if parent_dir == dir:
                parent_dir = ''
                
            self.goto_dir(parent_dir)

    def copyFile(self):
        path = self.txt_path_input.get()
        name = self.trv_fileExp.item(self.trv_fileExp.focus())['values']
        if name != '':
            name = name[0]
        else:
            return

        ext = os.path.splitext(name)[-1]
        description = (ext[1:].upper() + ' Files', "*" + ext)
        try:
            dest = asksaveasfilename(initialfile = name, defaultextension= ext, filetypes=[description], parent=self)
        except:
            return

        window = UI_copyFile(self, self.socket_queue, self.ui_queues, path, name, dest)
        window.grab_set()
        window.focus()

    def delete_file(self):
        return
    
    def update_dir(self, path):
        self.txt_path_input.configure(state = 'normal')
        self.txt_path_input.delete(0, tk.END)
        self.txt_path_input.insert(0, path)
        self.txt_path_input.configure(state = 'readonly')

    def update_tree(self, list_file):
        for file in list_file:
            self.trv_file_exp.insert('', tk.END, values = file)

    def clear_dir(self):
        self.update_dir(lb.WAIT)
        self.trv_file_exp.delete(*self.trv_file_exp.get_children())

    def goto_dir(self, dir):
        self.clear_dir()
        self.socket_cmd("update-dir", dir)

    def choose_in_tree(self, event):
        item = self.trv_file_exp.selection()[0]
        if self.trv_file_exp.item(item, "values")[2] in ("File folder", "Disk drive"):
            next_dir = os.path.join(self.txt_path_input.get(), self.trv_file_exp.item(item, "values")[0])
            self.goto_dir(next_dir)

    def update_ui(self, task):
        DEBUG("task", task)
        cmd, ext = task

        if cmd == "update-dir":
            path, list_file = ext
            self.update_dir(path)
            self.update_tree(list_file)

    def periodic_call(self):
        while True:
            try:
                task = self.ui_queue.get_nowait()
                self.update_ui(task)
                
            except queue.Empty:
                break
        
        self.after(const.UPDATE_TIME, self.periodic_call)
    
    def socket_cmd(self, cmd, ext = None):
        self.socket_queue.put((cmd, ext))

class UI_copyFile(tk.Toplevel):
    def __init__(self, parent, socket_queue, ui_queues, path, name, dest):
        self.ui_queue = queue.Queue()
        self.socket_queue = socket_queue
        ui_queues['copy-file'] = self.ui_queue

        super().__init__(parent)
        self.title = lb.COPY_FILE_TITLE
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.resizable(False, False)
        self['padx'] = const.WINDOW_BORDER_PADDING
        self['pady'] = const.WINDOW_BORDER_PADDING

        self.lbl_file_name_stt = tk.StringVar(self)
        self.lbl_file_name = tk.Label(self, textvariable=self.lbl_file_name_stt)
        self.lbl_file_name.grid(row = 0, column = 0, sticky = tk.W)

        self.lbl_file_size_stt = tk.StringVar(self, lb.FILE_SIZE)
        self.lbl_file_size = tk.Label(self, textvariable = self.lbl_file_size_stt)
        self.lbl_file_size.grid(row = 0, column = 1, sticky = tk.E)

        self.progress_bar = ttk.Progressbar(self, orient = tk.HORIZONTAL, length = 300, mode = 'determinate')
        self.progress_bar.grid(row = 1, column = 0, columnspan = 2, sticky = tk.EW, pady = (5,0))
        
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = 100
 
        self.btn_cancel = tk.Button(self, text = lb.CANCEL, command = self.cancel)
        self.btn_cancel.grid(row = 1, column = 2, sticky = tk.W, padx = (5,0), pady = (5,0), ipadx = 10)

        self.socket_cmd("copy-file", (os.path.join(path, name), dest))
        self.socket_cmd("continue-copy-file")
        self.after(const.UPDATE_TIME, self.periodic_call)


    def cancel(self):
        if(askokcancel(lb.CANCEL, lb.CANCEL_CONFIRM, parent = self)):
            self.destroy()

    def update_ui(self, task):
        DEBUG("task", task)
        cmd, ext = task

        if cmd == "get-info":
            if ext == "err":
                showwarning(lb.WARN, lb.COPY_FILE_FAIL, parent = self)
                self.destroy()
                return
            else:
                name, size = ext
                self.lbl_file_name_stt.set(name)
                self.lbl_file_size_stt.set(size)
        
        elif cmd == "create-file":
            if ext == "err":
                showwarning(lb.WARN, lb.COPY_FILE_FAIL, parent = self)
                self.destroy()
                return

        elif cmd == "copy-file":
            if ext == "err":
                showwarning(lb.WARN, lb.COPY_FILE_FAIL, parent = self)
                self.destroy()
                return
            elif ext == "done":
                showinfo(lb.INFO, lb.COPY_FILE_SUCCESS, parent = self)
                self.destroy()
                return
            else:
                size, percent = ext
                self.progress_bar['value'] = percent
                self.lbl_file_size_stt.set(size)
                self.socket_cmd("continue-copy-file")

    def periodic_call(self):
        while True:
            try:
                task = self.ui_queue.get_nowait()
                self.update_ui(task)
                
            except queue.Empty:
                break
        
        self.after(const.UPDATE_TIME, self.periodic_call)

    def add_socket_queue(self, socket_queue):
        self.socket_queue = socket_queue
    
    def socket_cmd(self, cmd, ext = None):
        self.socket_queue.put((cmd, ext))


def DEBUG(*args,**kwargs):
    print("File:", *args,**kwargs)