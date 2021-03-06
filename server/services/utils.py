from PIL import Image, ImageGrab
from datetime import datetime
from getmac import get_mac_address as gma
import os
import magic
import subprocess
import humanize
import win32com.client
import win32gui
import win32process
import win32api

#MAC
def get_MAC():
    return gma()

# screenshot
def take_screenshot(size=None):
    image = None
    try:
        image = ImageGrab.grab()
        w, h = image.size
        if size is not None:
            _w, _h = size
            if _h is not None:
                image = image.resize(size, Image.ANTIALIAS)
            else:
                scale = w / _w
                image = image.resize((int(w / scale), int(h / scale)), Image.ANTIALIAS)
    finally: 
        return image

# file
def get_all_disk_letters():
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]

    data_list = []
    for drive in drives:
        try:
            info = win32api.GetVolumeInformation(drive)
            data_list.append((drive, info[0], 'Disk drive', ''))
        except:
            pass
    return data_list

def get_dir(path):
    data_list = []
    if os.path.exists(path):
        with os.scandir(path) as it:
            for entry in it:
                try:
                    info = entry.stat()
                    modified = datetime.fromtimestamp(info.st_mtime).strftime('%d-%m-%Y %H:%M:%S')

                    if entry.is_file():
                        size = humanize.naturalsize(info.st_size)
                        type = magic.from_buffer(open(entry.path, "rb").read(2048))
                        data_list.append((entry.name, modified, type, size))
                    
                    if entry.is_dir():    
                        data_list.append((entry.name, modified, 'File folder', ''))
                except:
                    pass

    data_list.sort(key=lambda x: (x[2] != 'File folder', x[0].lower()))
    return data_list

def delete_file(path):
    try:
        os.remove(path)
    except:
        return False
    else:
        return True
        
class FileSender():
    def __init__(self, path):
        self.file = None
        self.path = path

    def open_file(self):
        try:
            self.file = open(self.path, 'rb')
        except:
            return False
        else:
            return True

    def close_file(self):
        self.file.close()

    def get_data(self, bytes = 1024):
        return self.file.read(bytes)

    def get_info(self):
        name = os.path.basename(self.path)
        size = os.path.getsize(self.path)
        return (name, size)

# app
def get_app_id():
    def getAllWindows(hwnd, result):
        name = win32gui.GetWindowText(hwnd)
        isVisible = win32gui.IsWindowVisible(hwnd)
        nID = win32process.GetWindowThreadProcessId(hwnd)

        if name != '' and isVisible:
            result.append(str(nID[1]))
        return True

    try:
        result = []
        win32gui.EnumWindows(getAllWindows, result)
        return result
    except:
        return []

def get_running_app():
    process = get_running_process()
    app_id  = get_app_id()

    result = []
    for line in process:
        if line[1] in app_id:
            result.append(line)

    return result

def get_target(file):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(file)
    return shortcut.Targetpath

def get_all_app():
    data_list = []
    try:
        for dir, folder, files in os.walk(os.path.expandvars('%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs')):
            for file in files:
                try:
                    if file.endswith('.lnk'):
                        target = get_target(os.path.join(dir, file))
                        if target.endswith('.exe'):
                            data_list.append((file[:-4], target))
                except:
                    pass
    finally:
        return data_list

# process
def get_result_from_cmd(cmd, headers):
    out = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,  stderr=subprocess.PIPE, stdin=subprocess.PIPE)

    lines = out.stdout.decode('utf-8').split('\r\n')

    firstLine = lines[0].rstrip()
    align = []
    for header in headers:
        align.append(firstLine.find(header))
    align.append(len(firstLine) + 1)
    
    result = []
    for line in lines[1:]:
        if line.rstrip():
            row = []
            for i in range(len(align) - 1):
                row.append(line[align[i] : align[i + 1] - 1].rstrip())
            result.append(row)

    return result
    
def get_running_process():
    try:
        return get_result_from_cmd('wmic process get description, processid, threadcount', ['Description', 'ProcessId', 'ThreadCount'])
    except:
        return []

def kill_process(pid):
    try:
        os.kill(int(pid), 9)
    except:
        return False
    else:
        return True

def start_process(path):
    try:
        subprocess.Popen(path)
    except:
        return False
    else:
        return True

# other   
def logout():
    try:
        os.system("shutdown -l")
    except:
        pass

def shutdown():
    try:
        subprocess.run(['shutdown', '-s', '-t', '0'])
    except:
        pass

def restart():
    try:
        os.system("shutdown /r /t 1")
    except:
        pass