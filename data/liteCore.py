# ======================================================================================================================
# NAME: DEX CORE - LITE VERSION
# FILE: liteCore.py
# DESC: The main file that is required for operation
#       Core file calls upon other files when needed.
# AUTH: Owen C. Easter
# COMP: EASTER LTD
# ======================================================================================================================

# IMPORT GENERAL ----------------------
import os
import cv2
import re
import sys
import time
import numpy
import random
import socket
import atexit
import datetime
import keyboard
import pythoncom
import speech_recognition as sr
# IMPORT FROM * -----------------------
from PyDictionary import PyDictionary
from _thread import start_new_thread
from threading import Thread
from forex_python.converter import CurrencyRates
# IMPORT GENERAL WEB-API --------------
import wikipedia
import webbrowser
from urllib import request
# IMPORTS FROM Dex4.* -----------------
import data.sqlmem as sql
from interface import web
from interface.osf import *
from lang.Dictionary import *
from lang.langModule import *
# IMPORTS FROM KIVY.XXX ---------------
from kivy.app import App

# ======================================================================================================================
# GUI INFORMATION --------------------:
is_alive = True
ChatHistory = ""

# SYSTEM INFORMATION -----------------:
# Global System Variables
Time = '00:00'
Date = '00-00-00'
version = '4 9 3 3'
version_check = 'Pass'

# Global Language Variables
L_say = ''
L_Input = ''
L_time = time.time()

# Global Listen Variables
count_nullInput = 0

# MODE LIST --------------------------:
# Modes enable non-essential functions
console_interface = False
alwaysListen_enabled = bool(sql.queryFor("SELECT value FROM variable_table WHERE name='#!hyperlisten'"))
vision_enabled = bool(sql.queryFor("SELECT value FROM variable_table WHERE name='#!vision'"))
passive_learning = bool(sql.queryFor("SELECT value FROM variable_table WHERE name='#!paslearning'"))
interactive_learning = bool(sql.queryFor("SELECT value FROM variable_table WHERE name='#!intlearning'"))
textChat_allowed = bool(sql.queryFor("SELECT value FROM variable_table WHERE name='#!webchat'"))

# MODE CONDITION GLOBALS -------------:
# must remain as false by default
textChat_enabled_temp = False
textChat_enabled = False

# USER INFORMATION -------------------:
# Always two user types, Master & User.

# MASTER USER ------------------------:
# Initiate Master File:
master_id = sql.query("SELECT * FROM master")
print('LOADING MASTER...', master_id)
if len(master_id) == 0:
    print(' > No Master Found.')
    print(' > Writing blank file')
    sql.query("INSERT INTO master VALUES(000, 'User', '', 'null', 1, '')")
    print(' > Loading new information.')
    master_id = sql.query("SELECT * FROM master")
    print(' > Success!')
    print('RELOADING MASTER...', master_id)

# Set Master Variables:
master_id = master_id[0]
master_name = str(master_id[1])
master_pass = str(master_id[3])
master_autoLogin = bool(master_id[4])
master_wloc = str(master_id[5])
master_id = int(master_id[0])

if master_wloc == '':
    master_wloc = None

# TARGET USER -----------------------:
# User designated per input
# default user is Master
user_id = master_id
user_name = master_name
user_wloc = master_wloc

# DEX-NET ----------------------------:
# Get the local IP of the system
local_ip = get_local_ip()
is_root = False
if local_ip.startswith("192"):
    # ROOT - am i the network Root?
    is_root = sql.query("SELECT value FROM variable_table WHERE name='#!is_root' LIMIT 1;")
    if not is_root: is_root = False
    else: is_root = True
    print("[DEXNET] is_root", is_root)
    root_adr = sql.queryFor("SELECT value FROM variable_table WHERE name='root_adr' LIMIT 1;")
    # Join Root-Network if available
    if root_adr is not None and root_adr is not []:
        root_adr = root_adr[0]
    elif is_root:
        root_adr = local_ip
    else:
        root_adr = None
    # Host if is_root:
    if root_adr is not None and root_adr.split(':')[0] == local_ip:
        if is_root:
            print('[DEXNET] Hosting as Root')
            subprocess.Popen("python -m http.server 4118")
        else:
            is_root = False
            sql.query("DELETE FROM variable_table WHERE name='#!is_root'")
    # Did your IP Change since last?
    if is_root and not local_ip == root_adr:
        root_adr = local_ip
        sql.query("UPDATE variable_table "
                  "SET value='" + local_ip + "'"
                  "WHERE name='root_adr' ")


# INTERFACE ============================================================================================================
# ORIGIN - DEXTER APP ------------------:
# Essential to starting operations
class coreApp(App):
    if system() == "Windows":
        title = 'Dexter ' + str(version)
        icon = './interface/Icons/easter.ico'
    else:
        title = "liteCore " + str(version)

    # BUILD FUNCTION
    def build(self):
        return self.running()

    # RUN CONSOLE INTERFACE
    def running(self):
        while is_alive:
            step()


# DEX CORE =============================================================================================================
# Core Functions are Essential to operation

# QUERY VOICE/TEXT INPUT ---------------:
# Only enabled when function is called
def query(raw_input, uid=master_id, username=master_name):
    global user_wloc, ChatHistory, Time, Date, textChat_allowed,\
            alwaysListen_enabled, user_id, user_name, textChat_enabled_temp, textChat_enabled,\
            master_wloc, threaded_response, L_say, L_Input, L_time, interactive_learning

    say = ''

    # === Who is talking === #
    textChat_enabled_temp = textChat_enabled
    user_id = uid
    user_name = username
    if user_id == master_id:
        user_wloc = master_wloc
        textChat_enabled = False
    else:
        user_wloc = None

    if raw_input == '#!weather':
        say = web.forecast_summary()
    elif raw_input == '#!recipe':
        r = web.get_easy_recipe()
        if not r[0] == '' and not r[1] == '':
            say = ["Hey " + user_name,
                   "How are you doing " + user_name,
                   "Hello, " + user_name,
                   user_name + '.']
            say = say[random.randint(0, len(say) - 1)] + '\nHow about trying some; ' + r[0] + '\n\n' + r[1]
        else:
            print('recipe:', r)
            say = "I am encountering some errors right now, send a tech monkey to help me please."

    # ============ CHAT LOG =============== #
    print(user_name + ': ' + str(remove_list(raw_input, junkSpecials)))

    # === CREATE CHAT RESPONSE === #
    threaded_response = ''

    def threaded_chat():
        global threaded_response
        threaded_response = chat(raw_input, username)

    chat_thread = Thread(target=threaded_chat, args=())
    if system() == "Windows":
        chat_thread.start()

    # ======== CLEAN INPUT ======== #
    # Adjusts text input for processing and fixes common mistakes in the speech recognition
    Input = remove_list(remove_list(' ' + str(raw_input).lower().
                                    replace("n't ", " not ") + ' ', specialChars), todWords).replace(" s ", " is ").\
        replace(" i m ", " i am ").replace(" ve ", " have ").replace('  ', ' ').replace(" whats ", " what ").\
        replace(" whos ", " who is ").replace(" hows ", " how is ").replace(" whys ", " why is ").\
        replace(" wheres ", " where is ").replace(' text or ', ' dexter ').replace(' re ', ' are ').\
        replace(' exeter ', ' dexter ').replace(' text to ', ' dexter ').replace(' sharpe ', ' shut up ').\
        replace(' d ', ' dexter ').replace(' whatsapp ', ' what is up ')

    # === ECHO CHECK === #
    if remove_list(L_say.replace(' ', '').lower(), specialChars) == \
            remove_list(raw_input.replace(' ', '').lower(), specialChars):
        print('[ECHO DETECTION] Canceled Input')
        return
    else:
        ChatHistory = ChatHistory + '\n' + user_name[:1].upper() + ': ' + raw_input

    # ========= SIMON SAYS ============ #
    # Repeat what the user said
    if Input.startswith(" say "):
        say = Input.replace(' say ', ' ')
        # ===== DEX SAY TO ____ ======= #
        for x in range(len(firstNames)):
            if firstNames[x] in say.title():
                target = firstNames[x]
                if 'everyone' in say.lower():
                    target = 'everyone'
                # Say ____ to ____
                if 'to ' in say or 'at ' in say or 'meet ' in say:
                    for y in range(len(greetingWords)):
                        if greetingWords[y] in say:
                            say = 'Hello, ' + target + '. Nice to meet you.'

    # ======== GREETINGS ========== #
    # Experimental function that speeds up simple chat
    if (Input in greetingWords and L_say not in greetingWords) and random.randint(0,2) > 0:
        say = raw_input.lower().replace('dexter', user_name)

    # ========= REMOVE JUNK =========== #
    # Removes useless words from text
    Input = remove_list(Input, junkWords)
    Input = remove_list(Input, greetingWords)

    # === MEMORY FUNCTIONS === # RE-WORK MEMORY FUNCTIONS TO ALLOW FOR MULTIPLE USERS????
    # STORE INFORMATION ----:
    if Input.startswith(rememberWords):
        r = remove_list(' ' + raw_input.lower() + ' ', rememberWords)
        sql.query("INSERT INTO triggers VALUES('remember','" + r + "','" + Date + " " + Time + "')")
        say = "Ok."

    # RECALL INFORMATION ---:
    # Recalls specified information the user has said
    elif is_list(Input, callMemoryWords):
        inn = remove_list(' ' + raw_input.lower() + ' ', callMemoryWords)
        r = sql.query("SELECT info FROM triggers")
        for i in range(len(r)):
            x = str(r[i]).replace("(' ", ' ').replace(" ',)", ' ')
            if inn.replace(' is ', ' ').replace(' my ', ' ') in x.replace(' is ', ' ').replace(' my ', ' '):
                say = swap_pov(x)

    # REMIND ME ------------:
    # Repeats information back to the user later
    elif Input.startswith(remindWords):
        r = remove_list(' ' + raw_input.lower() + ' ', remindWords)
        sql.query("INSERT INTO triggers VALUES('reminder', '" + r + "', '" + Date + " " + Time + "')")
        say = "I will remind you" + swap_pov(r)

    # ========= LANGUAGE INTERFACING OPTIONS ========= #
    # Create a temporary language input variable for
    # predictive correction based on language interfacing
    Inn = Input.replace('presenter', 'press enter')

    # DESKTOP INTERFACING ----:
    # Allows for interfacing with your desktop via voice
    tellWords = [" tell ", " inform ",
                 " notify ", " ask "]
    if Inn.startswith(" type "):
        i = 6
        j = len(Input)
        while i < j:
            key_press(str(Input[i]))
            i = i + 1

        return 'Ok.'
    elif Inn.startswith(" press "):

        key_press(str(Inn.replace(' press ', '')).replace('enter ', 'return').replace(' ',''))
        say = " "
    # Send some text to the users phone
    elif is_list(Input, sendToPhoneWords):
        Inn = remove_list(' '+raw_input.lower()+' ', sendToPhoneWords)
        tts('Ok.', True)
        web.push_notify(contents=Inn, uid=user_id)
        say = 'Done.'
    # Send a message to another user
    if is_list(Input, tellWords):
        task_complete = False
        people = sql.query("SELECT * FROM people")
        for word in tellWords:
            Inn = Input.split(word)
            if len(Inn) > 1:
                for person in people:
                    for I in Inn:
                        if I.startswith(person[1].lower()):
                            sql.query("UPDATE people "
                                      "SET tmsg='" + object_string_converter(' ' + raw_input.lower()
                                                                             + ' ', 'string') + "' "
                                      "WHERE name='" + person[1] + "'")
                            if random.randint(0, 3) < 3:
                                say = 'I will ' + word + ' ' + person[1] + ' that.'
                            else:
                                say = 'Sure thing.'
                            task_complete = True
            if task_complete:
                break

    # === LOCAL/MASTER EXCLUSIVE FUNCTIONS === #
    # Functions that can only be called locally
    if not textChat_enabled:
        # === OPEN LOCAL FILE === #
        if Input.startswith(' open '):
            try:
                Inn = remove_list(Input, openWords)

                core_dir = str(__file__).split('data\DexCore.py')[0]
                shortcuts = list_files('./interface/shortcuts')

                def do_open(path, cwd):
                    if textChat_enabled_temp:
                        web.push_notify(str(local_ip) + ':4117', uid=user_id)
                        share_directory(path=path)
                    else:
                        return osf_open(path=path)

                def search_dir(dir_searching, files, target=Inn):
                    global try_open, word_score, highest_word_score
                    try_open = ''
                    highest_word_score = 0
                    word_score = 0

                    if files is None:
                        return ''

                    for x in range(len(files)):

                        # MAKE FILE NAME READABLE
                        if '.' in files[x] and not files[x].startswith('.'):

                            # Remove file type from name
                            file = files[x].split('.')
                            if len(file) == 2:
                                file = file[0]
                            else:
                                new_file = ''
                                for y in range(len(file)):
                                    new_file = new_file + '.' + file[y]
                                file = new_file
                        else:
                            file = files[x]
                        file = file.lower().replace(' ', '')

                        if len(file.replace(' ', '')) < len(remove_list(target, junkWords).replace(' ', '')) / 2:
                            file = 'xyzIGNORE'

                        # Prioritize 'file name in input' searching
                        if file.lower() in target:
                            do_open(core_dir + dir_searching + files[x], dir_searching)
                            return 'Ok.'

                        # If not, check 'input in file name'
                        elif target.replace(' ','') in file.lower().replace(' ', ''):
                            do_open(core_dir + dir_searching + files[x], dir_searching)
                            return 'Got it.'

                        # Still not found anything? Check for matching words.
                        else:
                            if ' ' in target:
                                words = list(filter(None, target.split(' ')))
                                word_score = is_list(file, words, return_score=True)
                                if not word_score == 0:
                                    print('WORD SCORE:', word_score)
                                if word_score > 0:
                                    if word_score > highest_word_score:
                                        highest_word_score = word_score
                                        try_open = (core_dir + dir_searching + files[x])
                    return ''

                def search_drive(drive_letter):
                    return list_files(path=drive_letter+'://')

                # SEARCH SHORTCUTS FOLDER
                say = search_dir(dir_searching='interface/shortcuts/', files=shortcuts)

                if say == '' and system() == 'Windows':
                    dir_searching  = os.path.join(os.environ["HOMEPATH"], "Desktop")
                    core_dir = core_dir.split(':')[0] + ':'
                    shortcuts = list_files(str(core_dir) + str(dir_searching))
                    say = search_dir(dir_searching=dir_searching + '//', files=shortcuts)
                    if say == '':
                        dir_searching = dir_searching.replace("\Desktop", "")
                        shortcuts, folders = list_files(str(core_dir) + str(dir_searching), include_subdir=True)

                        for folder in folders:

                            if not folder.startswith('.') and not folder == 'Cookies':
                                shortcuts = list_files(dir_searching + '//' + folder)
                                say = search_dir(dir_searching=dir_searching + '//' + folder + '//', files=shortcuts)

                            if not say == '':
                                break

                        if say == '':
                            # if there was a predicted match: open it
                            if not try_open == '':
                                do_open(try_open, '')
                                say = 'Opening...'
                            else:
                                for x in range(len(alphaChars)):
                                    core_dir = ''
                                    drive = search_drive(alphaChars[x])
                                    if drive is not None:

                                        if say == '':
                                            dir_searching = str(alphaChars[x]) + ':'
                                            shortcuts, folders = list_files(dir_searching,
                                                                            include_subdir=True)
                                            say = search_dir(dir_searching=dir_searching + '//',
                                                             files=shortcuts)
                                            if say == '':
                                                for folder in folders:
                                                    print(folder)
                                                    shortcuts = list_files(path=dir_searching + '//' + folder + '//')
                                                    print(str(dir_searching + '//' + folder))
                                                    say = search_dir(dir_searching=dir_searching + '//' + folder + '//',
                                                                     files=shortcuts)
                                                    print(str(dir_searching + '//' + folder + '//'))
                                                    if not say == '':
                                                        break

                        if say == '':
                            # if there was a low-confidence match: open match
                            if not try_open == '':
                                do_open(try_open, '')
                                say = 'Opening...'
            except Exception as e:
                report(exception=e, running="open query")
        elif Input.startswith(' close '):
            i = Input.split(' close ')[1]
            if i in getProcesses():
                os.system("TASKKILL /F /im " + i + ".exe")
                say = 'Got it.'
            else:
                say = "Sorry, i couldn't find that process."
        # === MEDIA FUNCTIONS === #
        # Previous:
        if is_list(Input, mediaPrevious) or Input == ' previous ' or Input == ' back ':
            keyboard.press_and_release('previous track')
            keyboard.press_and_release('previous track')
            say = " "
        # REPEAT -:
        elif is_list(Input, mediaLoop):
            keyboard.press_and_release('previous track')
            say = " "
        # PLAY ---:
        elif is_list(Input, mediaPlay) or Input == ' play ' or Input == ' start ':
            if system() == 'Windows':
                if is_media():
                    keyboard.press_and_release('play/pause media')
                else:
                    openAPPDATA("\Spotify\SpotifyLauncher.exe")
                    tts('Opening Spotify')
                    time.sleep(10)
                    keyboard.press_and_release('play/pause media')
            else:
                keyboard.press_and_release('play/pause media')
            say = " "
        # PAUSE --:
        elif is_list(Input, mediaPause) or Input == ' pause ' or Input == ' stop ':
            keyboard.press_and_release('play/pause media')
            say = " "
        # NEXT ---:
        elif is_list(Input, mediaNext) or Input == ' next ' or Input == ' skip ' or Input == ' skipped ' or \
                Input == ' skipp':
            keyboard.press_and_release('next track')
            say = " "
        # MUTE ---:
        elif is_list(Input, mediaMute) or Input == ' mute ' or Input == ' silence ' or Input == ' be silent ':
            keyboard.press_and_release('volume down')
            keyboard.press_and_release('volume mute')
            say = "mute"
        # UNMUTE -:
        elif is_list(Input, mediaUnmute) or is_list(Input, mediaPlay):
            keyboard.press_and_release('volume mute')
            keyboard.press_and_release('volume up')
            say = "unmuted."
        # Volume -:
        elif is_list(Input, mediaVU) or is_list(Input, mediaVD) or Input == ' up ' or Input == ' down ':
            if is_list(Input, mediaVU) or ' up ' in Input:
                x = 'up'
            else:
                x = 'down'
            i = 0
            if is_list(Input, desc_lesser):
                while i < 3:
                    keyboard.press_and_release('volume ' + x)
                    i = i + 1
            elif is_list(Input, desc_greater):
                while i < 20:
                    keyboard.press_and_release('volume ' + x)
                    i = i + 1
            else:
                while i < 9:
                    keyboard.press_and_release('volume ' + x)
                    i = i + 1
            say = " "

        # ====== ALARM FUNCTION ====== #
        if is_list(Input, alarmWords):
            Inn = remove_list(Input.lower(), digits)
            # Figure Out the Time Format
            if "a.m" in Inn or " am " in Inn:
                format = 12
                am = True
            elif "p.m" in Inn or " pm " in Inn:
                format = 12
                am = False
            else:
                format = 24
                am = None
            # Get Input Time
            Inn = Input.lower()
            alarm = ''
            for char in Inn:
                if is_list(char, digits):
                    alarm = alarm + char
            # Figure out the Time to Set
            if format == 24 and len(str(alarm)) == 1:
                sql.query("INSERT INTO variable_table VALUES('alarm', '" + str(alarm) + ":00')")
                say = "Alarm set for " + str(alarm) + str(am)
                if int(Time.split(':')[0]) >= int(alarm):
                    say = say + ", Tomorrow."
            else:
                say = "Alarm functions are not working right now."

        # ===== SMART HOME CONTROLLER ===== #
        if is_list(Input, smartdeviceWords) and (is_list(Input, addWords) or ' scan' in Input):
            sql.query("DELETE FROM smart_devices")
            tts("Scanning for compatible devices now.", True)
            hs100('', 'scan')
            if lifx('scan'):
                tts("I found Smart Lights on the local network and they are ready for use.")
                sql.query("DELETE FROM smart_devices"
                          "WHERE name='lifx_lan_controller'")
                sql.query("INSERT INTO smart_devices VALUES('lifx_lan_controller', 'N/A')")
            say = " "

        # ON/OFF LIFX BULBS
        elif ' light' in Input or ' bulb' in Input:
            if is_list(Input, onWords):
                lifx('on')
                say = 'Ok.'
            elif is_list(Input, offWords):
                lifx('off')
                say = 'Ok.'
            if ' dim ' in Input:
                lifx('dim')
                say = 'Ok.'
            elif ' bright' in Input or ' brian ' in Input or ' britain ' in Input:
                lifx('bright')
                say = 'Ok.'

        # ON/OFF HS100 DEVICES
        elif ' on ' in Input or ' off ' in Input:
            sdl = SmartDeviceList()
            print(sdl)
            for x in range(0, len(sdl)):
                if sdl[x][0] in Input:
                    Inn = Input.replace(sdl[x][0], '')
                    print(Inn)
                    device_ip = sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[0]
                    if ' on ' in Inn:
                        hs100(target_ip=device_ip, option='on')
                        say = "Ok."
                    elif ' off ' in Inn:
                        hs100(target_ip=device_ip, option='off')
                        say = "Ok."

        # ===== ENABLE VISION ===== #
        elif ' vision ' in Input or ' version ' in Input:
            global vision_enabled
            if is_list(Input, onWords):
                if vision_enabled:
                    say = "Vision is already enabled."
                else:
                    vision_enabled = True
                    say = "VISION: ENABLED."

            if is_list(Input, offWords):
                if vision_enabled:
                    vision_enabled = False
                    say = "VISION: DISABLED."
                else:
                    say = "Vision is already disabled"

        # ==== ENABLE WEB_CHAT ==== #
        elif is_list(Input, webChatWords):
            if is_list(Input, offWords) or is_list(Input, noWords):
                textChat_allowed = False
                say = "Ok, stopping all online conversations."
            else:
                if not textChat_allowed:
                    textChat_allowed = True
                    say = "I am now allowing online conversations."
                else:
                    say = "I'm already allowing online conversations."

        # ==== ENABLE ALWAYS_LISTEN ==== #
        elif is_list(Input, alwaysListenWords):
            if is_list(Input, offWords):
                alwaysListen_enabled = False
                say = "HYPER LISTEN: DISABLED"
            else:
                alwaysListen_enabled = True
                say = "HYPER LISTEN: ENABLED"

        # ==== ENABLE INTERACTIVE_LEARNING ==== #
        elif 'interactive learning' in Input:
            if is_list(Input, onWords):
                if not interactive_learning:
                    interactive_learning = True
                    say = "INTERACTIVE LEARNING: ENABLED"
                else:
                    say = "Interactive learning is already enabled."
            elif is_list(Input, offWords):
                if interactive_learning:
                    interactive_learning = False
                    say = "INTERACTIVE LEARNING: DISABLED"
                else:
                    say = "Interactive learning is already disabled"

        # ==== ENABLE INTERACTIVE_LEARNING ==== #
        elif 'passive learning' in Input:
            global passive_learning

            if is_list(Input, onWords):
                if not passive_learning:
                    passive_learning = True
                    say = "PASSIVE LEARNING: ENABLED"
                else:
                    say = "Passive learning is already enabled."
            elif is_list(Input, offWords):
                if passive_learning:
                    passive_learning = False
                    say = "PASSIVE LEARNING: DISABLED"
                else:
                    say = "Passive learning is already disabled"

        # === SHUTDOWN FUNCTION === #
        elif 'system' in Input or 'computer' in Input:
            if Input.replace(' computer ', ' ').replace(' system ', ' ') in killWords:
                if system() == 'Windows':
                    tts('system shut down T minus 10 seconds.')
                    os.system('shutdown /s 10')
                    say = ' '
                else:
                    say = "I don't know how to turn off this system."
            if is_list(Input, rebootWords):
                if system() == "Linux":
                    tts(string="rebooting system.")
                    os.system("sudo reboot")
                elif system() == "Windows":
                    tts(string="rebooting system")
                    os.system("shutdown -g")
        elif Input in killWords:
            say = ' '
            end()
        elif Input in rebootWords:
            tts(string="Rebooting Platform...")
            os.execl(sys.executable, sys.executable, *sys.argv)

        # ========= STOP TALKING ========== #
        elif Input.startswith(stopWords):
            print('== SILENCE ==')
            if system() == 'Windows':
                while 'espeak.exe' in getProcesses():
                    os.system("TASKKILL /F /im espeak.exe")
                say = 'Ok.'

    # ============ MATH =============== #
    Inn = raw_input.replace("'", "").replace('is equal to', '=').replace('equal to', '=').\
        replace('equals', '=').replace('equal', '=').replace(' = ', '=').replace(' =', '=').replace('= ', '=').\
        replace('Equals', '=').replace('Equal', '=').replace(' is ', '=').replace('?', '').replace(' plus ', ' + ').\
        replace(' negative ', ' - ').replace(' divide', ' /').replace(' add ', ' + ')
    # FETCH VARIABLES -:
    if '=' in Input or 'equal' in Input or ' is ' in Input and is_list(Input, digits):
        # print('searching for variables')
        Inn = Inn.replace('=',' = ').split(' ')
        var_name = ''
        var_value = None
        for x in range(len(Inn)-2):
            if Inn[x] == '=':
                try:
                    if not Inn[x-1] == 'what':
                        var_name = '#!' + Inn[x-1]
                        var_value = int(remove_list(Inn[x+1], alphaChars).replace(' ',''))
                        print(var_name, var_value)
                    if not var_name == '' and var_value is not None and not var_value == '':
                        sql.query("DELETE FROM variable_table WHERE name='"+var_name+"'")
                        sql.query("INSERT INTO variable_table VALUES('" + var_name + "', '" + str(var_value) + "')")
                        Inn[x], Inn[x-1], Inn[x+1] = '', '', ''
                except:pass
        if say == '' and var_name is not None and var_value is not None:
            say = "ok."
        Inn = ' '.join(Inn)+' '
    # CALCULATE ----:
    if '*' in Inn or '+' in Inn or '^' in Inn or '/' in Inn or '-' in Inn or '=' in Inn:
        try:
            # REPLACE VARIABLES:
            r = sql.query("SELECT * FROM variable_table WHERE name LIKE '%#!%'")
            que = Inn.replace(' ', '').replace('x', '*').replace('*', ' * ').replace('^', '**').replace('÷', '/').\
                replace('times', '*').replace('plus', '+').replace('minus', '-').replace('negative', '-').\
                replace('multiply', '*').replace(' divide', '/').replace('=', '').replace('+', ' + ').\
                replace('**', ' ** ').replace('/', ' / ')
            for x in range(len(r)):
                que = que.replace(' ' + r[x][0].replace('#!', '') + ' ', r[x][1])
            ans = str(eval(remove_list(que, alphaChars).replace(' ', '')))
            if not ans == que:
                say = ans
                print(que + ' = ' + say)
        except:
            pass

    # === GENERAL FUNCTIONS === #
    if is_list(Input, callWords) and say == '':
        # TIME AND DATE --------------------------------
        if ' time ' in Input:
            m = ' A.M. '
            Time = Time.split(':')
            if int(Time[0]) > 12:
                Time[0] = str(int(Time[0]) - 12)
                m = ' P.M. '
            Time = ':'.join(Time)
            say = say+'The time is ' + Time + m
        if ' date ' in Input:
            Date = Date.split('-')
            prefix = 'th'
            if int(Date[2][-1:]) == 1:
                prefix = 'st'
            if int(Date[2][-1:]) == 2:
                prefix = 'nd'
            if int(Date[2][-1:]) == 3:
                prefix = 'rd'
            Date[2] = str(int(Date[2]))
            Year = Date[0]
            Date = str(Date[2] + prefix + ' of ' +
                       Date[1].
                       replace('01', 'January').
                       replace('02', 'February').
                       replace('03', 'March').
                       replace('04', 'April').
                       replace('05', 'May').
                       replace('06', 'June').
                       replace('07', 'July').
                       replace('08', 'August').
                       replace('09', 'September').
                       replace('10', 'October').
                       replace('11', 'November').
                       replace('12', 'December'))
            if 'time' in say:
                say = say + 'and the date is, the '+Date+', '+Year
            else:
                say = say+'It is the '+Date+', '+Year+'. '

        # DICTIONARY -----------------------------------
        if ' meaning of ' in Input or ' definition of ' in Input or (' does ' in Input and ' mean ' in Input):
            try:
                dic = PyDictionary()
                i = remove_list(Input, callWords)
                word = i.replace('meaning','').replace('does','').replace('mean','').replace('definition','').\
                    replace(' by ',' ').replace(' of ',' ').replace(' ','')
                i = str(dic.meaning(word)).split(']')
                print(i)
                i = i[0].replace('{','').replace('[','').replace('(','').replace(']','').replace('}','').\
                    replace("',","',\n").replace(':','. meaning: ')
                print(i)
                if i == "None":
                    say = "I'm not sure."
                else:
                    say = word + " is a " + i
            except Exception as e:
                print(e)

        # VERSION REPORTING ----------------------------
        if ' version ' in Input and say == '':
            say = 'Version: ' + str(version)

        # SYSTEM NAME ------------------
        if ' name ' in Input and (' system ' in Input or ' computer ' in Input):
            say = say + 'This systems name is: '+str(socket.gethostname())

        # SYSTEM LOCAL IP --------------
        if ' local ' in Input and ' ip ' in Input:
            say = say + local_ip

        # SYSTEM GLOBAL IP -------------
        elif ' ip ' in Input:
            try:
                say = say + str(web.get_ip())
            except:
                say = "There is no valid internet connection avalible to me right now."

        # SYSTEM PROCESSES -------------
        if ' processes ' in Input or ' process ' in Input:
            say = getProcesses()

        # SYSTEM SCREEN SHOT -----------
        if ' screenshot ' in Input or ' screen shot ' in Input:
            scr_screenshot(str(time.time()))
            say = 'Got it.'

        # =========== CHIT CHAT ================ #
        # TELL ME A JOKE ---------------
        if ' joke ' in Input:
            say = jokeList[random.randint(0, len(jokeList) - 1)]
            if say in ChatHistory:
                say = jokeList[random.randint(0, len(jokeList) - 1)]

        # MEANING OF LIFE --------------
        if ' meaning of life ' in Input:
            say = meaningLife

        # GOODBYE ----------------------
        if Input == ' goodbye ':
            say = 'goodbye.'

    # === WEB FUNCTIONS === #
    if Input.startswith(searchWords) and say == '':
        tts('Searching...', True)
        search = remove_list(Input, searchWords).replace('  ', '')

        result = sql.queryFor("SELECT url FROM bookmarks WHERE name='" + search + "'")
        if result is not None:
            if not textChat_enabled:
                webbrowser.open_new_tab(result[0])
                say = " "
            else:
                say = result[0]
        else:
            r, result = web.search(search)
            if not textChat_enabled and not textChat_enabled_temp:
                webbrowser.open_new_tab(result)
                if r.domain in search:
                    say = "Opening " + r.domain
                else:
                    say = "I found something on " + r.domain + '.' + r.suffix
            else:
                say = result
            # SAVE SEARCH RESULT TO MAKE FUTURE RESULTS FASTER
            sql.query("INSERT INTO bookmarks VALUES('" + search + "', '" + result + "', '')")

    # ============== TTS ================= #
    if say == '':
        if interactive_learning:
            if is_list(string=Input, word_list=callWords) and not is_list(string=Input, word_list=personalWords)\
                    and not 'do you' in raw_input.lower() and not 'your' in raw_input.lower():
                say = get_wiki(remove_list(remove_list(Input, callWords), junkWords))

    if say == '':
        say = chat(str(raw_input), username=user_name)

    # GENERATE SPEECH ---------------------:
    # If no output has been decided upon
    train_data = False

    if system() == "Windows":
        if say == '':
            train_data = True
            chat_thread.join(timeout=120.0)

        if say == '':
            say = threaded_response

        if not say == '':
            if train_data and interactive_learning\
                    and not raw_input == '#!weather':
                if (time.time() - L_time) < 500 and not L_say == '':
                    print('training multi-line conversational data.')
                    start_new_thread(train_conversation, ([L_say, raw_input, say], ))
                else:
                    print('training single-line conversational data')
                    start_new_thread(train_conversation, ([raw_input, say], ))

    # Confirm Action if Silent Response & Text Chat Enabled
    if say == " " and textChat_enabled_temp:
        say = "Ok."

    # END QUERY PROCESS -------------------:
    # Reset textChat var for non-local master
    textChat_enabled = textChat_enabled_temp
    # Generates output text as voice if local or as text-message if not
    tts(say, False)

    # Returns output as string
    L_time = time.time()
    L_say = say
    L_Input = raw_input
    print(Input, say)
    return say


# STEP - RUN CONSTANT ------------------:
# Main function operating at all times
def step():
    global Time, Date, textChat_allowed, textChat_enabled, local_ip, root_adr
    # CHECK DATABASE FOR START-UP MESSAGES
    r = bool(sql.queryFor("SELECT value FROM variable_table WHERE name='is_restart_update'"))
    print('IS_RESTART:', r)
    if r is True:
        web.push_notify(contents=str(socket.gethostname()) + " is back online.", uid=master_id)
        sql.query("DELETE FROM variable_table WHERE name='is_restart_update'")

    # BACKGROUND PROCESSES
    if system() == 'Windows':
        if passive_learning:
            start_module(LearningCore)
        if vision_enabled:
            start_module(VisionCore)
        if textChat_allowed:
            start_module(web.login_fbm)
        start_module(listen)

    ignored_processes = ['svchost', 'ctfmon', 'nvcontainer', 'settingsynchost',
                         'sihost', 'shellexperiencehost', 'smss', 'csrss', 'wininit', 'winlogon', 'services',
                         'lsass', 'fontdrvhost', 'dwm', 'wudfhost', 'spoolsv', 'securityhealthservice',
                         'dashost', 'msdtc', 'dllhost', 'sgrmbroker', 'searchindexer',
                         'tasklist', 'conhost', 'fsnotifier64', 'taskhostw', 'systemsettings', 'searchfilterhost',
                         'wmiprvse', 'messagingapplication', 'runtimebroker', 'winstore.app',
                         'applicationframehost', 'hxtsr', 'msascuil', 'searchui', 'lockapp', 'audiodg', 'microsoft.photos',
                         'searchprotocolhost', 'explorer', 'crashreporter', 'taskmgr', 'rundll32', "b'", 'werfault',
                         'video.ui', 'oawrapper', 'nvoawrappercache', 'backgroundtaskhost', 'sppsvc', 'smartscreen',
                         'sppextcomobj', 'compattelrunner', 'trustedinstaller']
    online = False

    # TICK COUNTER
    last_tick = '00:00'
    last_time = 0

    # === CHECK FOR & RESPOND TO MESSAGES === #
    # Update WebChat Contacts
    def updated_contacts():
        return web.action_fbm(action='fetch_all', user_id=master_id), sql.query("SELECT * FROM people")
    active_chat, contacts = updated_contacts()

    # Chat with user
    def chat_window(new_id, new_name):
        global textChat_enabled
        if not str(new_id) in str(active_chat):
            return
        dex_prev = object_string_converter(
            sql.queryFor("SELECT info FROM people WHERE uid=" + str(new_id))[0],
            in_type='object')
        try:
            web_Input = web.action_fbm(action='fetch', user_id=new_id)
            if Time.startswith('15:') and '1' not in str(sql.query("SELECT weather FROM people WHERE uid='" + str(new_id) + "'")):
                if '1' not in str(sql.query("SELECT weather FROM people WHERE uid='" + str(new_id) + "'")):
                    sql.query("UPDATE people SET weather=1 WHERE uid='" + str(new_id) + "'")
                    textChat_enabled = True
                    web.action_fbm(action='mark', user_id=new_id)
                    dex_prev = object_string_converter(
                        query(raw_input='#!weather', username=new_name, uid=new_id))
                    sql.query("UPDATE people "
                              "SET info='" + str(dex_prev) + "' "
                              "WHERE uid='" + str(new_id) + "'")
            elif Time.startswith('16:'):
                if '1' not in str(sql.query("SELECT recipe FROM people WHERE uid='" + str(new_id) + "'")):
                    sql.query("UPDATE people SET recipe=1 WHERE uid='" + str(new_id) + "'")
                    if random.randint(0, 30) <= 3:
                        textChat_enabled = True
                        web.action_fbm(action='mark', user_id=new_id)
                        dex_prev = object_string_converter(
                            query(raw_input='#!recipe', username=new_name, uid=new_id))
                        sql.query("UPDATE people "
                                  "SET info='" + str(dex_prev) + "' "
                                  "WHERE uid='" + str(new_id) + "'")
            elif not web_Input.lower() == dex_prev.lower():
                textChat_enabled = True
                web.action_fbm(action='mark', user_id=new_id)
                dex_prev = object_string_converter(
                    query(raw_input=web_Input, username=new_name, uid=new_id))
                sql.query("UPDATE people "
                          "SET info='" + str(dex_prev) + "' "
                          "WHERE uid='" + str(new_id) + "'")
            else:
                if not Time.startswith('15:'):
                    sql.query("UPDATE people SET weather=0 WHERE uid='" + str(new_id) + "'")
                if not Time.startswith('16:'):
                    sql.query("UPDATE people SET recipe=0 WHERE uid='" + str(new_id) + "'")
        except Exception as e:
            if str(e).startswith("Could not fetch thread"):
                return False
            if str(e) == "'NoneType' object has no attribute 'replace'":
                return False
        textChat_enabled = False

    # STEP LOOP
    while True:
        try:
            # ====== SET TIME & DATE ====== #
            Time = str(datetime.datetime.now().time()).split('.')[0].split(':')
            Time = str(int(Time[0])) + ':' + str(Time[1])
            Date = str(datetime.date.today())
            current_datetime = Date + ' ' + Time
            s = int(time.time())

            # DO ROUTINE TASKS ----:
            if not Time == last_tick or not last_time == s:
                if isinstance(last_tick, str):
                    last_tick = last_tick.split(':')
                t = Time.split(':')

                # CONSTANT - PER HOUR
                if not t[0] == last_tick[0]:
                    last_tick[0] = t[0]

                    # Update Local Network IP
                    local_ip = get_local_ip()
                    if local_ip.startswith('192'):
                        online = True
                    else:
                        online = False

                    if online:
                        if lifx('scan'):
                            sql.query("DELETE FROM smart_devices"
                                      "WHERE name='lifx_lan_controller'")
                            sql.query("INSERT INTO smart_devices VALUES('lifx_lan_controller', 'N/A')")
                        hs100(target_ip='', option='scan', commanded=False)

                    # Update Contacts
                    if textChat_allowed and online:
                        active_chat, contacts = updated_contacts()

                # CONSTANT - PER MINUTE
                elif not t[1] == last_tick[1]:
                    last_tick[1] = t[1]
                    # ALARM
                    i = sql.query("SELECT * FROM variable_table WHERE name='alarm'")
                    for a in i:
                        if a[1] == Time:
                            if not is_media():
                                openAPPDATA("\Spotify\SpotifyLauncher.exe")
                            for i in range(100):
                                keyboard.press_and_release("volume_down")
                            time.sleep(1)
                            for i in range(25):
                                keyboard.press_and_release("volume_up")
                            tts(string="Good Morning " + user_name, main_thread=True)
                            time.sleep(2)
                            if int(t[0]) < 12:
                                a = ' A.M.'
                                ta = str(int(t[0])).replace('0', '12')
                            else:
                                a = ' P.M.'
                                ta = str(int(t[0]) - 12).replace('0', '12')
                            tb = str(t[1])
                            tts(string="It is " + ta + ':' + tb + a,
                                main_thread=True)
                            if is_media():
                                keyboard.press_and_release('play/pause media')
                            else:
                                openAPPDATA("\Spotify\SpotifyLauncher.exe")
                                tts('Opening Spotify')
                                time.sleep(10)
                                keyboard.press_and_release('play/pause media')
                    # Windows Only support for Process Spectator
                    if system() == 'Windows':
                        # UPDATE PROCESSES RECORDS ---:
                        processes = getProcesses().split('\\r\\n')
                        found_processes = []
                        for p in processes:
                            p = p.split('.')

                            if len(p) > 1:
                                p[-1] = p[-1].split(' ')
                                p_type = []
                                for x in p[-1]:
                                    if not x == '':
                                        p_type.append(x)
                                p_mem = p_type[4]
                                p_type = p_type[0]

                                if len(p) > 2:
                                    p.remove(p[-1])
                                    p = '.'.join(p)
                                else:
                                    p = p[0]
                                if not [p, p_type] in found_processes and not p in ignored_processes:
                                    found_processes.append([p, p_type])
                        # RECORD PROCESS INFORMATION IN THE TABLE
                        if len(found_processes) > 1:
                            for process in found_processes:
                                # Find the process in the table
                                q = sql.queryFor("SELECT * FROM processes WHERE process='" + process[0] + "'")
                                # Add process to table if it isn't there
                                if not bool(q):
                                    sql.query("INSERT INTO processes VALUES('" + process[0] + "','"
                                              + process[1] + "', '" + current_datetime + "', '0,0,0')")
                                # Update the process in table if it is there
                                else:
                                    # Get Time Running
                                    active = str(q[3]).replace('[','').replace(']','').split(',')
                                    if not len(active) == 3:
                                        active = [0,0,0]
                                    # Update minutes running
                                    a = int(active[2]) + 1
                                    # Update hours running
                                    if a >= 60:
                                        active[1] = int(active[1]) + 1
                                        active[2] = 0
                                    # Update days running
                                    if int(active[1]) >= 24:
                                        active[0] = int(active[0]) + 1
                                        active[1] = 0
                                    # Update Database /w new Information
                                    sql.query("UPDATE processes "
                                              "SET active='"+str(active[0])+','+str(active[1])+','+str(active[2]) +
                                              "' WHERE process='" + q[0] + "'")
                    # MANAGE OWENS ROOM LIGHTS
                    sdl = SmartDeviceList()
                    for x in range(0, len(sdl)):
                        if sdl[x][0] == 'lamp':
                            device_ip = sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[
                                0]
                            if Time == '5:59':
                                hs100(target_ip=device_ip, option='on')
                                for x in range(0, len(sdl)):
                                    if sdl[x][0] == 'desktop':
                                        hs100(target_ip=sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[0],
                                              option='on')
                            elif Time == '8:00':
                                for x in range(0, len(sdl)):
                                    if sdl[x][0] == 'desktop':
                                        hs100(
                                            target_ip=sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[0],
                                            option='off')
                            elif Time == '8:20':
                                lifx(option='off')
                                hs100(target_ip=device_ip, option='off')
                            elif Time == '16:15':
                                lifx(option='bright', rapid=True)
                                hs100(target_ip=device_ip, option='off')
                                for x in range(0, len(sdl)):
                                    if sdl[x][0] == 'desktop':
                                        hs100(
                                            target_ip=sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[0],
                                            option='on')
                            elif Time == '23:00':
                                lifx(option='off')
                                hs100(target_ip=device_ip, option='off')
                                for x in range(0, len(sdl)):
                                    if sdl[x][0] == 'desktop':
                                        hs100(
                                            target_ip=sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[0],
                                            option='off')

                # CONSTANT - PER SECOND
                elif not last_time == s:
                    # UPDATE SECONDS
                    last_time = s
                    # WEB CHAT IF ALLOWED
                    if textChat_allowed and online:
                        try:
                            # If there are active conversations
                            if active_chat is not None and contacts is not None:
                                # If there are no Messenger Contacts
                                if len(contacts) == 0:
                                    for x in range(len(active_chat)):
                                        is_active = str(active_chat[x]).split('<USER ')[1].split(')>')[0].split(' (')
                                        if not is_active[1] in str(contacts):
                                            is_active[0] = is_active[0].split(" ")
                                            print('ADDING USER:', is_active[0])
                                            sql.query("INSERT INTO people "
                                                      "VALUES(" + is_active[1] + ",'" + is_active[0][0] + "','" +
                                                      is_active[0][-1] + "', '', 0, '')")
                                            contacts = sql.query("SELECT * FROM people")
                                            break
                                # Check Conversations
                                for i in range(len(contacts)):
                                    contact = contacts[i]
                                    for x in range(len(active_chat)):
                                        is_active = str(active_chat[x]).split('<USER ')[1].split(')>')[0].split(' (')
                                        if contact[0] == int(is_active[1]):
                                            chat_window(contact[0], contact[1])
                                        if not is_active[1] in str(contacts):
                                            is_active[0] = is_active[0].split(" ")
                                            print('ADDING USER:', is_active[0])
                                            sql.query("INSERT INTO people "
                                                      "VALUES(" + is_active[1] + ",'" + is_active[0][0] + "','" +
                                                      is_active[0][-1] + "', '', 0, '')")
                                            contacts = sql.query("SELECT * FROM people")
                                            break
                            else: active_chat, contacts = updated_contacts()
                        except Exception as e:
                            report(running="Messenger", exception=e)
                    # UPDATE VI INDEX -----:
                    update_index(version=version, Date=Date, Time=Time, is_root=is_root)

                last_tick = ':'.join(last_tick)

        except Exception as e:
            report("Step Function", exception=e)


# START MODULE - BEGIN NEW THREAD ------:
# Parent function creates new threads
def start_module(process, parameters=()):
    print(">> START MODULE:", process)
    return start_new_thread(process, parameters)


# VOICE ENGINE =========================================================================================================
# Text to speech & sound engine functions

# LISTEN TO MICROPHONE -----------------:
# Only disabled on request
def listen():
    global tab_press
    # check for microphone
    mic = sr.Microphone(1)
    # set recognition_engine
    raw = sr.Recognizer()
    # set push_to_talk
    tab_press = False

    # PROCESS FUNCTION ---:
    def process(audio):
        global ChatHistory, count_nullInput, tab_press
        # raw_input equals text returned by engine
        raw_input = ''
        # Attempt to process audio file
        try:
            raw_input = raw.recognize_google(audio)
        except Exception as e:
            e = str(e)
            if not e == '' and count_nullInput < 2:
                # Error Number 11001 equals No Internet Connection
                if '[Errno 11001]' in e:
                    count_nullInput = 100
                    report("listen", "cannot connect with Google Cloud.")
                # Bad Gateway equals weak connection or exclusive error
                elif 'Bad Gateway' in e:
                    count_nullInput = count_nullInput + 1
                    report("listen", "experiencing connection problems.")
                # Otherwise report the error to the local user
                else:
                    report("speech recognition", e)
        # If no speech was recognized
        if raw_input == '' and not tab_press:
            # Return Negative
            return False
        # If some speech was recognized
        else:
            # If the user has recently spoken to V.I.
            if alwaysListen_enabled or tab_press:
                # process the input text as query
                query(raw_input=raw_input)
                # reset null input counter
                count_nullInput = 0
                tab_press = False
            # If the user has not recently spoken to V.I.
            else:
                # If check contains V.I. name or nickname
                if is_list(' ' + raw_input.lower() + ' ', nameWords):
                    if alwaysListen_enabled:
                        count_nullInput = 0
                    else:
                        count_nullInput = 2
                    # process the input text as query
                    query(raw_input=raw_input)
                # else:
                # print("Heard but not registered:", raw_input)
            # Return Positive
            return True
        # END OF PROCESS

    # KEY INPUT LISTENER
    def on_tab(key):
        global tab_press
        if str(key).endswith('down)'):
            tab_press = True

    def on_sl(key):
        if str(key).endswith('down)'):
            sdl = SmartDeviceList()
            for x in range(0, len(sdl)):
                if sdl[x][0] == 'desktop':
                    hs100(target_ip=sql.queryFor("SELECT ip FROM smart_devices WHERE name='" + sdl[x][0] + "'")[0],
                          option='toggle')

    keyboard.hook_key('`', on_tab, True)
    keyboard.hook_key('scroll lock', on_sl, True)

    online = False
    while is_alive:
        if not online:
            s = socket.gethostbyname(socket.gethostname())
            if s.startswith('192'):
                online = True
        if online and (tab_press or alwaysListen_enabled):
            try:
                # record audio using microphone
                with mic as source:
                    # audio equals sound file to be processed
                    audio = raw.listen(source=source)
                    # process audio in the background
                    if alwaysListen_enabled and not tab_press:
                        start_new_thread(process, (audio, ))
                    else:
                        start_new_thread(process, (audio,))
                        s = socket.gethostbyname(socket.gethostname())
                        if not s.startswith('192'):
                            online = False
            except: online = False
        elif not online:
            i = input()
            query(raw_input=i)


# SPEECH MODULE ------------------------:
# Cannot be disabled
def tts(string, main_thread=False, reset_count=True):
    # Should other functions wait for speech to end?
    # > No (may cause V.I. to talk over itself)
    if main_thread is False:
        return start_new_thread(tts, (string, True, reset_count))
    global ChatHistory, count_nullInput
    text = remove_list(string, junkSpecials)
    # > Update graphical chat log with output text
    if not text == ' ' or text == '':
        ChatHistory = ChatHistory + '\n' + '[D]: ' + text
    # > If V.I. is talking to local user then reset count
    if reset_count is True and not textChat_enabled:
        count_nullInput = 0
    # > If V.I. is not talking to local user then text to speech is not executed
    if textChat_enabled or textChat_enabled_temp:
        # send facebook message to non-local user
        web.action_fbm(action='send', user_id=user_id, msg=text.lower())
        # update console chat log with output text
        print('[D]:', text)
    # > Execute Speech
    elif main_thread is True:
        if system() == 'Windows':
            os.system("TASKKILL /F /im espeak.exe")
        lang_tts(text)


# ERROR REPORTING ----------------------:
# Cannot be disabled
def report(running, exception):
    # convert Running into language ->
    run = running
    if run == 'routine/news':
        run = "a routine news update,"
    if run == 'routine/weather':
        run = "a routine weather update,"
    # convert Exception into language ->
    error = str(exception)
    if "codec can't encode character" in error:
        error = "I couldn't translate the text from key_code into english."
    if error == '':
        error = "I ran into an un-identifiable error."
    if "[Errno 11001]" in error:
        error = "There was a connection failure."
    # Create error report
    error_report = 'While running ' + str(run) + '\n' + str(error)
    print(error_report)


# LEARNING ENGINE ======================================================================================================
# All functions related to learning or information parsing

# WIKI SEARCH --:
# Returns a summary of a wiki-page based on query
def get_wiki(question):
    # Init variables
    say = ''
    Inn = ''
    # This code might not find anything, but that's ok.
    try:
        # What piece of information is the query asking for.
        Inn = question
        # If no subject was found, skip this entire function.
        if not Inn == '':
            # Check database for related information
            #i = sql.queryFor("SELECT * FROM bookmarks "
            #                 "WHERE name LIKE '%" + Inn + "%' "
            #                 "OR url LIKE '%" + Inn.replace(' ', '_') + "%'")
            i = None
            if i is not None and len(i) == 4:
                if i[1] == 'n/a' and i[2] == 'n/a':
                    return ''
                else:
                    say = object_string_converter(i[2], 'object')
            else:
                if get_local_ip().startswith('192'):
                    res = wikipedia.search(Inn)
                    i, j = 0, len(res)
                    while i < j:
                        res[i] = res[i].lower().split(' ')
                        i = i + 1
                    if len(res) == 0:
                        res = web.webq(web.search, p1=Inn, p2=True, p3=False, timeout=3)
                else:
                    return say

                # SELECT BEST SUBJECT
                if len(res) > 1:
                    hs = ['', 0]
                    for subject in res:
                        s = 0
                        for word in subject:
                            if word in Inn:
                                s = s + 1
                            elif word not in Inn:
                                s = s - 0.75
                            if Inn == word:
                                s = s + 4
                            if len(subject) == 1 and word == Inn:
                                s = s + 6
                            if ' '.join(subject) == Inn:
                                s = s + 8
                        if s > hs[1]:
                            hs[0], hs[1] = ' '.join(subject), s
                    if hs[1] >= len(hs[0].split(' ')) / 1.5:
                        res = hs[0]
                else:
                    res = ' '.join(res[0])

                # GET SELECTED SUBJECT
                if not res == '':
                    result = wikipedia.summary(remove_list(res.replace('%', ''), digits)) \
                        .replace(' ( listen); ', '').replace('( listen))', '') \
                        .replace(' ( or US: ) ', ' ').replace('(;','(')
                    result = result.encode('ascii', 'ignore').decode('ascii').split('. ')
                    if len(result) > 1:
                        say = str(result[0]) + '. ' + str(result[1]) + '.'
                    else:
                        say = str(result[0])

                    if len(say) < 450 and len(say + str(result[2])) < 450 and len(result) > 4:
                        say = say + ' ' + str(result[2]) + '.'
                        if len(say) < 450 and len(say + str(result[3])) < 450:
                            say = say + ' ' + str(result[3])
                    sql.queryFor("INSERT INTO bookmarks VALUES('" + Inn + "','" + res[0].lower() + "', '" +
                                 object_string_converter(say, 'string') + "', '1')")
                    if not Inn.lower() == res[0].lower().replace('_', ' '):
                        sql.queryFor("INSERT INTO bookmarks VALUES('" +
                                     res[0].lower().replace('_', ' ') + "','" +
                                     res[0].lower() + "', '" +
                                     object_string_converter(say, 'string') + "', '1')")

    except Exception as e:
        report('an online information search', e)
        print('00', str(e).encode('utf-8'))
        say = ''

    # Pre-Defined info snippets
    # Born, Died, Birthday...etc
    if not say == '':
        say = say.split('. ')
        for x in range(len(say)):
            print(say[x])
            i = re.split("[()\[\]]+", say[x])
            if len(list(i)) > 2:
                if is_list(i[1], digits):
                    if 'born' in i[1] or 'birth' in i[1] or 'death' in i[1] or 'died' in i[1] or ' - ' in i[1]:
                        say[x] = ''.join(i)
                        if 'born' in question or 'birthday' in question or 'died' in question or 'dead' in question:
                            return ''.join([i[0], i[1]])
                    else:
                        say[x] = ''.join([i[0], i[1], i[2]])
                else:
                    say[x] = ''.join([i[0], i[2]])
            else:
                say[x] = ''.join(i)
        say = '. '.join(say)

    # If nothing can be found, mark this as n/a
    elif say == '' and not Inn == '':
        sql.query("INSERT INTO bookmarks VALUES('" + Inn + "', 'n/a', 'n/a', '1')")
    print('WIKI_SEARCH RESULT:', say)
    return say


# DEFINE ON EXIT/KILL/CRASH ============================================================================================
# On Code Failure or Manual Shutdown this code is to be executed


# ON END -----------------------------:
# Cannot be disabled
def end():
    global interactive_learning, passive_learning, vision_enabled, textChat_allowed, is_alive
    print('[ROOT] Saving sys.info to database')
    # Saves Master Information
    sql.query("DELETE FROM master")
    sql.query("INSERT INTO master VALUES('"+str(master_id)+"', 'User', 'User', null, 1, '')")
    # Clears temp object memory
    sql.query("DELETE FROM variable_table WHERE name LIKE '%#!%'")
    # Saves web chat mode to table
    if is_root:
        sql.query("INSERT INTO variable_table VALUES('#!is_root', 'True')")
    sql.query("DELETE FROM variable_table WHERE name='root_adr'")
    sql.query("INSERT INTO variable_table VALUES('root_adr', '"+str(root_adr)+"')")
    if textChat_allowed: sql.query("INSERT INTO variable_table VALUES('#!webchat', 'True')")
    if interactive_learning: sql.query("INSERT INTO variable_table VALUES('#!intlearning', 'True')")
    if passive_learning: sql.query("INSERT INTO variable_table VALUES('#!paslearning', 'True')")
    if vision_enabled: sql.query("INSERT INTO variable_table VALUES('#!vision', 'True')")
    if alwaysListen_enabled: sql.query("INSERT INTO variable_table VALUES('#!hyperlisten', 'True')")
    # Close database connection
    sql.close_database()
    # Exit Application
    if system() == "Windows":
        os.system("TASKKILL /F /IM phantomjs.exe")
    coreApp.get_running_app().stop()
    interactive_learning = False
    passive_learning = False
    vision_enabled = False
    textChat_allowed = False
    is_alive = False
    print('[ROOT] waiting on threads...')
    tts(string="Goodbye.", main_thread=True)
    time.sleep(3)
    print('[ROOT] Success! Shutting down platform...')
    exit()


# Learning Core
class LearningCore:

    def __init__(self):
        self.study_target = None
        self.last_study = ""
        self.WikiStudy()

    def WikiStudy(self):
        while is_alive:
            if passive_learning:
                try:
                    self.study_target = None
                    while self.study_target is None:
                        i = wikipedia.random().lower()
                        if remove_list(remove_list(i, alphaChars), digits).replace(' ', '') == "":
                            self.study_target = i
                    print(">> STUDY TARGET:", self.study_target)
                    result = wikipedia.summary(self.study_target.replace(' ', '_')) \
                        .replace(' ( listen); ', '').replace('( listen))', '') \
                        .replace(' ( or US: ) ', ' ').replace('(;', '(').replace('(Arabic:', '') \
                        .replace(') )', '')
                    result = result.encode('ascii', 'ignore').decode('ascii').split('. ')
                    if len(result) > 1:
                        result = str(result[0]) + '. ' + str(result[1]) + '.'
                    else:
                        result = str(result[0])
                    print(">> Result", result)
                    sql.query("DELETE FROM bookmarks WHERE name='" + self.study_target + "'")
                    sql.query("INSERT INTO bookmarks "
                              "VALUES('" + self.study_target +
                              "', '" + self.study_target.replace(' ', '_') +
                              "', '" + object_string_converter(result, 'string') + "', '1')")
                except:
                   pass


# Vision Core
class VisionCore:

    def __init__(self):
        self.input = scr_get()
        self.passive_study()

    def passive_study(self):
        while is_alive:
            if vision_enabled:
                zone_of_focus = winMousePosition()
                zone_of_focus = [zone_of_focus['x']-10, zone_of_focus['y']-10,
                                 zone_of_focus['x']+10, zone_of_focus['y']+10]
                self.visual_study(region_to_study=zone_of_focus)

    def visual_study(self, region_to_study):
        # OBTAIN INPUT DATA
        print('STUDYING REGION:', region_to_study)
        t = [time.time(), 0, 0]
        self.input = numpy.asarray(scr_region(region_to_study))
        data = []
        t[1] = time.time()
        print('CAPTURE TIME:', time.time() - t[0])
        for l in self.input:
            data.append([])
            for p in l:
                data[-1].append(int((p[0] + p[1] + p[2])/3))
            print(data[-1])
        t[2] = time.time()
        print('PRE-PROCESSING TIME:', t[2] - t[1])
        # SEARCH FOR SHAPES IN THE NUMBERS AND STUFF
        print('TOTAL TIME ELAPSED :', t[2] - t[0])


# [END OF ESSENTIAL liteCore FUNCTIONALITY]

# DISPLAY PROFILE SETTINGS ON LAUNCH ----------------------------------
print('LOADING PROFILES...')
print('     is_root :', is_root)
print('     Vision  :', vision_enabled)
print('     Web Chat:', textChat_allowed)
print('     Hyper Listen:', alwaysListen_enabled)
print('     Int Learning:', interactive_learning)
print('     Pas Learning:', passive_learning)
tts(string='Hello.')

# END OF FILE [liteCore.py]
