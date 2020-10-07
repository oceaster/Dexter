# LANGUAGE MODULE
from platform import system
from subprocess import call
from chatterbot import ChatBot
from chatterbot.response_selection import get_first_response
from chatterbot.trainers import ListTrainer

# Dictionary module used for pronunciation
# ** Why is this here? what the F does it do?
import nltk

# Running this on startup will keep it up-to-date
# ** But why do you need to update this??
# ** Gonna test if this is needed by running without on the Pi
# nltk.download('punkt')

# OS DEPENDENT
# Chooses synthesizer based on Operating System
if system() == 'Windows':
    synth = "./win_dex/winsyn/command_line/espeak.exe"
else:
    synth = "espeak"

# GLOBALS
# Variables control voice settings
voice = "en+m1"
amp = "190"
pitch = "44"
speed = "180"
line_break = "1"


# CREATE VOICE INSTANCE
# RUN Voice Synthesizer
def lang_tts(string):
    text = string

    if not text.replace(' ', '') == '':
        # TRY print encoded text
        try:
            print("VI: " + text)
        # EXCEPT non-decodable text
        except Exception as e:
            print(e)
            print("VI: [print error]")

    # REPLACE case sensitive text WITH case sensitive text
    text = text.replace(' US ', ' U.S. ').replace(' UK ', ' U.K. ').replace('Vi ',' V i ').replace(' eta ', ' E.T.A ').\
        replace('USD', 'U.S.D').replace('km/s', 'kilometers per second').replace('mi/s', 'miles per second').lower()

    # REPLACE lower case text WITH lower case text
    text = text.replace(' ii ', ' the second ').replace(' iii ', ' the third ').replace(' iv ', ' the fourth ').\
        replace("'m ", " am ").replace("'ve ", " have ").replace("'ll ", " will ").replace("'d ", " would ").\
        replace("'re ", " are ").replace(' f*** ', ' fuck ').replace(' f****** ', ' fucking ').\
        replace(' - ', ' minus ').replace("'.", "' ").replace(".'", "' ").replace('. ','.\n').replace(" im ", " i am ")

    # SEND STRING TO SPEECH SYNTH
    call([synth, "-v", voice, "-a", amp, "-p", pitch, "-s", speed, "-l", line_break,
          text])


# CREATE CHAT BOT INSTANCE
# returns responses to chat input
dex = ChatBot("Dexter",
              trainer='chatterbot.trainers.ChatterBotCorpusTrainer',
              storage_adapter='chatterbot.storage.SQLStorageAdapter',
              response_selection_method=get_first_response,
              preprocessors=[
                  'chatterbot.preprocessors.clean_whitespace',
                  'chatterbot.preprocessors.unescape_html',
                  'chatterbot.preprocessors.convert_to_ascii'
              ],
              filters=[
                   "chatterbot.filters.RepetitiveResponseFilter"
              ],
              logic_adapters=[
                  {
                      "import_path": "chatterbot.logic.BestMatch",
                  },
              ],
              database='./data/memory.db',
              read_only=False
              )


# USE FOR TRAINING CONVERSATION DIALOGUE
# trains the chat bot on a list of strings
def train_conversation(data):
    dex.set_trainer(ListTrainer)
    dex.train(data)


# STRING / DATABASE OBJECT CONVERTER
# makes strings database friendly and easy to parse
def object_string_converter(string, in_type='string'):
    output = string
    obj_list = [('"', '#!dq'), ("'", "#!sq"), (',', '#!cm'), (';', '#!sc'), ("`", "#!sq"), ('"', '#!dq'),
                ('.', '#!sp')]
    if in_type == 'string':
        for x in range(len(obj_list)):
            output = output.replace(obj_list[x][0], obj_list[x][1])

    elif in_type == 'object':
        for x in range(len(obj_list)):
            output = output.replace(obj_list[x][1], obj_list[x][0])
    return output


# CHAT FUNCTION
def chat(user_input, username='user'):
    # Respond
    response = dex.\
        get_response(user_input.replace(' d ','#!Yname').replace('dexter', '#!Yname').replace('Dexter', '#!Yname').\
        replace(' f*** ', ' fuck ').replace(' f****** ', ' fucking ').replace(username, '#!Mname'))
    return str(response).replace('#!Mname', 'Dexter').replace('#!Yname', username)


# REMOVE LIST OF ITEMS FROM A STRING
def remove_list(string, word_list):
    x = string
    for word in word_list:
        x = x.replace(word, ' ')
    return x


# CHECK IF STRING MATCHES ANY LIST CONTENTS
def is_list(string, word_list, return_score=False):
    x = False
    if return_score:
        x = 0
    for i in range(len(list(word_list))):
        if word_list[i] in string:
                if not return_score:
                    return True
                else:
                    x = x + 1
    return x


# ME -> YOU
def swap_pov(string, third_person=False):
    x = string
    if third_person is True:
        x = x.replace(' i ', ' #!Yname ')
    x = x.replace(' i ', ' you ')
    if third_person is True:
        x = x.replace(' am ', ' is ')
    x = x.replace(' am ', ' are ')
    if third_person is True:
        x = x.replace(' my ', " #!Yname's ")
    x = x.replace(' my ', ' your ')
    if third_person is True:
        x = x.replace(' me ', " #!Yname ")
    x = x.replace(' me ', ' you ')
    x = x.replace(' you you ', ' you, that you ')
    # THEN SWITCH YOU / YOUR's that were there before
    y = string.split(' ')
    x = x.split(' ')
    for i in range(len(y)):
        if y[i] == x[i]:
            if (y[i] == 'you' and y[i+1] == 'are') or ('you' in y[i] and 're' in y[i]):
                x[i] = x[i].replace('you', 'i')
                x[i] = x[i].replace("'", ' ')
                x[i] = x[i].replace("re", 'am')
                x[i+1] = x[i+1].replace('are', 'am')
            if y[i] == 'you' and y[i+1] == 'have':
                x[i] = x[i].replace('you', 'i')
            if y[i] == 'you':
                x[i] = x[i].replace('you', 'me')
            if y[i] == 'your':
                x[i] = x[i].replace('your', 'my')
    x = ' '.join(x)
    return x

# END OF FILE [langModule.py]
