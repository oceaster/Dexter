# === OPERATING SYSTEM FUNCTIONS === #
# IMPORTS FROM SYSTEM
import os
import socket
import keyboard
import subprocess
from data.sqlmem import query
from ctypes import windll, Structure, c_long, byref
# IMPORTS FROM SMART HOME
import lifxlan
from pyHS100 import smartplug
# IMPORTS FOR DESKTOP-PLATFORM
if not socket.gethostname() == "raspberrypi":
    import pyscreenshot as ScreenGrab
# LIFX_LAN Object
lifx_controller = lifxlan.LifxLAN()

# LOCAL NETWORK FUNCTIONS --------------------------:
def get_local_ip(return_self=True):
    # Method 1: Not always compatible
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    # Method 2: Not always Accurate
    except Exception as e:
        print(e, '[IP EXCEPTION] Using socket.gethostbyname() instead')
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception as e:
            print(e, '[IP EXCEPTION] No network.')
            local_ip = '0.0.0.0'

    if return_self:
        return local_ip
    else:
        local_ip = local_ip.split('.')
        return local_ip[0] + '.' + local_ip[1] + '.' + local_ip[2]


# SMART DEVICE FUNCTIONS -----------------------------:

# SMART DEVICES LIST
# Returns all known smart devices registered in the DB
def SmartDeviceList():
    return query("SELECT * FROM smart_devices ORDER BY LENGTH(name) DESC")


# CONTROL LIFX DEVICES
# Requires no information
def lifx(option, dlight=23000, blight=65535, fade=0, rapid=True):
    try:
        # SCAN NETWORK
        if option == 'scan':
            return bool(lifx_controller.discover_devices())
        # POWER ON/OFF
        elif option == 'on':
            return lifx_controller.set_power_all_lights(1, 2, False)
        elif option == 'off':
            return lifx_controller.set_power_all_lights(0, 2, False)
        # BRIGHTNESS OPTIONS
        elif option == 'dim':
            lifx_controller.set_power_all_lights(1, 2, False)
            return lifx_controller.set_color_all_lights([0, 0, dlight, 3000], fade, rapid)
        elif option == 'bright':
            lifx_controller.set_power_all_lights(1, 2, False)
            return lifx_controller.set_color_all_lights([0, 0, blight, 5700], fade, rapid)
        # FETCH DEVICE INFO
        elif option == 'get':
            return [list(lifx_controller.get_color_all_lights().values())[0][2],
                    list(lifx_controller.get_power_all_lights().values())[0]]
    except Exception as e:
        print(e)
        return False


# CONTROL HS100/HS110 DEVICES
# Requires the device local IP
def hs100(target_ip, option, local_ip=get_local_ip(return_self=False) + '.', commanded=True):
    try:

        # SCAN Local Network for devices
        if option == 'auto-scan' or option == 'scan':
            from data.sqlmem import query
            known_devices = query("SELECT * FROM smart_devices")

            def threaded_scan(minimum, maximum):
                from lang.langModule import lang_tts
                from interface.web import push_notify
                response_list = ''
                x = minimum
                y = maximum
                while x <= y:
                    try:
                        ping = smartplug.SmartPlug(local_ip+str(x))
                        response = ping.sys_info
                        if not bool(query("SELECT * FROM smart_devices WHERE name='"+response['alias'].lower()+"'")):
                            query("DELETE FROM smart_devices "
                                  "WHERE name='" + response['alias'].lower() + "'")
                            query("DELETE FROM smart_devices "
                                  "WHERE ip='" + local_ip + str(x) + "'")
                            query("INSERT INTO smart_devices "
                                  "VALUES('" + response['alias'].lower() + "', '" + local_ip + str(x) + "')")
                            response_list = response_list + '\n----------\nNAME: ' + response['alias'] + '\nIP: ' + local_ip + str(x)
                            if commanded:
                                lang_tts("I found a device called '" + response['alias'] + "'.")
                    except Exception as e:
                        if local_ip.startswith('127.0.0'):
                            return False
                        elif not str(e).startswith('Communication error'):
                            print('while scanning for smart devices on the local network\nERROR:', e)
                    x = x + 1
                if 'IP:' in response_list and not str(known_devices) == str(query("SELECT * FROM smart_devices")):
                    if len(response_list.split('IP:')) > 2:
                        push_notify(contents="I found these smart devices on the local network "
                                             "and configured them for use."
                                             + response_list)
                    else:
                        push_notify(contents="I found this smart device on the local network and configured it for use."
                                             + response_list)
                print("[FINISHED] Smart Scan " + str(minimum) + '-' + str(maximum))

            from threading import _start_new_thread
            _start_new_thread(threaded_scan, (0, int(255*0.2)))
            _start_new_thread(threaded_scan, (int((255*0.2)+1), int(255*0.4)))
            _start_new_thread(threaded_scan, (int((255*0.4)+1), int(255*0.6)))
            _start_new_thread(threaded_scan, (int((255*0.6)+1), int(255*0.8)))
            _start_new_thread(threaded_scan, (int((255*0.8)+1), int(255)))

        # Target Smart Plug
        device = smartplug.SmartPlug(target_ip)

        # Turn target ON
        if option == 'on':
            return device.turn_on()

        # Turn target OFF
        elif option == 'off':
            return device.turn_off()

        # Get status of Device
        elif option == 'status':
            return device.state

        elif option == 'power':
            return device.current_consumption()

        elif option == 'toggle':
            print(device.state)
            if device.state == 'ON':
                return device.turn_off()
            else:
                return device.turn_on()

    # REPORT ERROR
    except Exception as e:
        if not option == 'status':
            print('smart device communication error: ',e)
        else:
            return False


# V.I. NETWORK FUNCTIONS ------------------------------:
# FIND LOCAL ROOT NETWORKS
# Requires a local network
def root_scan(action='find'):
    from urllib.request import urlopen
    lp = get_local_ip(return_self=False) + '.'
    for x in range(255):
        s = lp + str(x)
        print("[ROOT SCAN] on", s)
        try:
            if action == 'find':
                u = urlopen(url="http://" + s + ":4118/data/index.ini", timeout=0.4).read().decode('utf-8')
                if "root=1" in u:
                    return u
            if action == 'fetch':
                u = urlopen(url="http://" + s + ":4118/data/shared.ini", timeout=1).read().decode('utf-8')
                fetched = []
                if 'news=' in u:
                    fetched.append(u.split('news=')[1].split('[[~!END!~]]')[0])
                else:
                    fetched.append('None')
                if 'weather=' in u:
                    fetched.append(u.split('weather=')[1].split('[[~!END!~]]')[0])
                else:
                    fetched.append('None')

                return fetched

        except Exception as e:
            print(e)
            pass

    return ''


# LOCAL SYSTEM & APPLICATIONS ------------------------:
# Functions related to controlling local system / OS

# GET all running processes on the host system
def getProcesses():
    processes = \
    subprocess.Popen('tasklist', stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0]
    processes = str(processes).lower()
    return processes


# OPEN object by path
def osf_open(path):
    print('opening dir '+path)
    return os.startfile(path)


# OPEN object within WINDOWS appdata dir
def openAPPDATA(path):
    print('opening AppData dir ' + path)
    return os.startfile(os.getenv('APPDATA') + path)


# OPEN object within WINDOWS local appdata dir
def openLOCALAPPDATA(path):
    print('opening LocalAppData dir ' + path)
    return os.startfile(os.getenv('LOCALAPPDATA') + path)


# LISTS all the files & folders in a directory
def list_files(path, include_subdir=False):

    for root, dirs, files in os.walk(path):
        f_count = []
        for f in files:
            f_count.append(f)

        if not include_subdir:
            return f_count

        d_count = []
        for d in dirs:
            d_count.append(d)

        return f_count, d_count


# CHECKS if there is media playing on the device
def is_media(spotify=False):
    p = getProcesses()
    if "spotify.exe" in p:
        return True
    elif spotify:
        return False
    elif "wmplayer.exe" in p:
        return True
    elif "music.ui.exe" in p:
        return True
    elif "vlc.exe" in p:
        return True
    else:
        return False


# SCREEN INTERACTIONS --------------------------------:
# SAVES a screen shot to local dir
def scr_screenshot(name):
    return ScreenGrab.grab().save('./interface/screenshots/' + name + '.bmp')


# RETURNS the screen as a variable
def scr_get():
    return ScreenGrab.grab()


# RETURNS the screen and saves to a directory
def scr_save(dir):
    return ScreenGrab.grab_to_file(dir)


# RETURNS the screen a section of the screen as a variable
def scr_region(bbox):
    return ScreenGrab.grab(bbox=bbox)


# ENABLES use of shift-keys
def key_press(key):
    if key in ['£', '$', '%', '^', '&', '*', '(', ')', '"', "'", '!', '@', ':', '~', '}', '{', '_', '+', '¬', '?', '<', '>']:
        keyboard.press("shift")
        keyboard.press_and_release(key)
        keyboard.release("shift")
    else:
        keyboard.press_and_release(key)


p0 = None
p1 = None
python_command = 'python'


def share_directory(path='C:/', port=4118):
    global p0, p1, python_command
    # Default update_port
    update_port = 4118
    # Kill current host if not None
    if port == update_port:
        if p0 is not None:
            p0.kill()
            p0 = None
    else:
        p1.kill()
        p1 = None
    # Set working directory
    wd = os.getcwd()
    # Go to target location
    os.chdir(path)
    # Try share directory locally
    try:
        print('[DEXNET] Sharing', path)
        if port == update_port:
            print("[DEXNET]", python_command + " -m http.server " + str(update_port))
            p0 = subprocess.Popen(python_command + " -m http.server " + str(update_port))
        else:
            p1 = subprocess.Popen(python_command + " -m http.server " + str(port))
    except Exception as e:
        print('[DEXNET]', e)
        try:
            print('[DEXNET] Attempting to share directory...')

            # Change python path command
            if python_command == 'python':
                python_command = 'python3'
            else:
                python_command = 'python'

            # Try again with new command
            if port == update_port:
                p0 = subprocess.Popen(python_command + " -m http.server " + str(update_port))
            else:
                p1 = subprocess.Popen(python_command + " -m http.server " + str(port))

            print('[DEXNET] found', python_command, 'in path')
        except Exception as e:
            print('[DEXNET]', e)
    # Return to working directory
    os.chdir(wd)


def update_index(version, Date, Time, is_root):
    global my_file_list
    folder = list_files('./', True)
    my_file_list = ''

    def select_item(f, is_dir, tree=''):
        global my_file_list
        for x in range(len(f)):
            if not f[x].startswith('.') and not f[x].endswith('.log') and not \
                    f[x].endswith('.ini') and not f[x].startswith('_') and not \
                    f[x] == 'Browser' and not f[x] == 'winsyn' and not f[x] == 'screenshots' and not \
                    f[x] == 'shortcuts' and not f[x].endswith('.db') and not f[x].endswith('.db-shm'):
                if is_dir:
                    f1 = list_files('./' + tree + f[x] + '/', is_dir)
                    new_tree = tree + f[x] + '/'
                    if f1[0] is not None:
                        select_item(f1[0], is_dir=False, tree=new_tree)
                    if f1[1] is not None:
                        select_item(f1[1], is_dir=True, tree=new_tree)
                else:
                    my_file_list = my_file_list + tree + f[x] + ','

    select_item(folder[0], is_dir=False)
    select_item(folder[1], is_dir=True)

    index_content = "ver=" + str(version) + \
            "\nlabel=Alpha Mercury" + \
            "\nip=" + str(socket.gethostbyname(socket.gethostname())) + \
            "\nhost=" + str(socket.gethostname()) + \
            "\nstamp=" + Date + ' ' + Time + \
            "\nroot=" + str(is_root) + \
            "\nlist=" + my_file_list
    index_file = open('./data/index.ini', 'w')
    index_file.write(index_content)


def update_shared(news=None, weather=None):
    index_content = "[SHARING]"

    if news is not None:
        index_content = index_content + 'news=' + news + '[[~!END!~]]'
    if weather is not None:
        index_content = index_content + 'weather=' + weather + '[[~!END!~]]'

    index_file = open('./data/shared.ini', 'w')
    index_file.write(index_content)


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


def winMousePosition():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return {"x": pt.x, "y": pt.y}


# END OF FILE [osf.py]
