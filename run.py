# ======================================================================================================================
# PROJECT: DEXTER
# RELEASE: Alpha Mercury
# BUILD  : June 2018
# DEPENDENCIES: Kivy, speechrecognition, weather-api, webbrowser, sqlite3, chatterbot, googletrans, hyper
#               phantom-js, espeak, python-forex, keyboard, pyscreenshot, open cv2, numpy, pyHS100, wikipedia,
#               lifxlan
# AUTHOR: OWEN CAMERON EASTER
# ======================================================================================================================

import subprocess
import platform
import os
from socket import gethostname


# CONSOLE - HIDE CMD WINDOWS FOR WINDOWS:
def hide_console():
    if platform.system() == 'Windows':
        import win32console,win32gui
        window = win32console.GetConsoleWindow()
        win32gui.ShowWindow(window,0)
        return True


# Main Function -------------:
# Imports & Launches Core File
if __name__ == "__main__":

    while True:
        try:
            hide_console()
            from data import liteCore
            liteCore.coreApp().run()
            break
        except Exception as e:
            print('Failed to spark DexCore: ', str(e))

            if str(e).startswith("No module named '"):
                print('     > Install', str(e).split("'")[1])
                command = "pip install --upgrade " + str(e).split("'")[1]. \
                    replace('speech_recognition', 'speechrecognition'). \
                    replace('weather', 'weather-api'). \
                    replace('newspaper', 'newspaper3k'). \
                    replace('kivy',
                            'docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew '
                            'kivy.deps.gstreamer kivy.deps.angle kivy'). \
                    replace('cv2', 'opencv-python').replace('pyaudio',
                                                            'libportaudio2 incremental setuptools buildtools pyaudio').\
                    replace('pyHook', './data/source_libs/pyHook-1.5.1-amd64.whl')
                if platform.system() == 'Windows':
                    subprocess.call(command)
                else:
                    command = command.replace('PIL', 'pillow')
                    command = command.replace(' pypiwin32 ', ' ')
                    os.system(command.replace('pip ', 'sudo pip3 '))
            else:
                print('     > Fatal Error')
                break

            if gethostname() == "raspberrypi":
                os.system("sudo pip3 install lxml==3.4.4")
                os.system("sudo apt-get build-dep python-imaging")
                os.system("sudo apt-get install libopenjp2-7")
                os.system("sudo apt-get install libjpeg62 libjpeg62-dev libtiff5 libxml2-dev libxslt-dev python-dev")

# MERCURY - OPEN LETTER ================================================================================================
# No clear objective for this release.
# ======================================================================================================================

# END OF FILE [run.py]
