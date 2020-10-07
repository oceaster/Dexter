# === GENERAL IMPORTS === #
# Last modified: 04308
import time
import json
import smtplib
import requests
from platform import system
# === DEX IMPORT === #
from data import sqlmem
from lang.Dictionary import junkSpecials
from lang.langModule import remove_list, object_string_converter
# === WEB IMPORTS === #
import tldextract
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver as wd
# === NEWS IMPORTS === #
from newspaper import Article
# === MESSENGER IMPORTS === #
from fbchat import Client
from fbchat.models import *

# CHOOSES A BROWSER BASED ON OPERATING SYSTEM
if system() == 'Windows':
    browser = wd.PhantomJS('./win_dex/Browser/phantomjs.exe')
else:
    browser = wd.chrome

# GMAIL USERNAME / PASSWORD V.I. can access
email_username = ''
email_password = ''
# PUSH OVER ADDRESS for push notifications
pushover_adr = ''
# FACEBOOK account details V.I. can access
fb_email = 'oceaster@outlook.com'
fb_pass = sqlmem.query("SELECT value FROM variable_table WHERE name='#!fbmp'")
if bool(fb_pass):
    fb_pass = fb_pass[0]
# QUEUE A WEB ACTION
# declare global variable
busy = False


# QUEUE A WEB ACTION
# define function for web_queue
def webq(web_function, p1=None, p2=None, p3=None, timeout=30):
    global busy

    start_time = time.time()

    while busy:
        if time.time() > start_time + timeout and not timeout == 0:
            return False
        else:
            print('browser waiting...')

    busy = True

    if p3 is not None:
        r = web_function(p1, p2, p3)
    elif p2 is not None:
        r = web_function(p1, p2)
    elif p1 is not None:
        r = web_function(p1)
    else:
        r = web_function()

    busy = False

    return r


# RETURNS CURRENT SYSTEM IP
# NOT LOCAL
def get_ip():
    url = 'http://ipinfo.io/json'
    response = requests.get(url)
    data = json.loads(response.text)
    IP = data['ip']
    return IP


# RETURNS CURRENT GEO LOCATION
# LONGITUDE / LATITUDE
def get_lonlat():
    url = 'http://freegeoip.net/json'
    response = requests.get(url)
    data = json.loads(response.text)
    lat = data['latitude']
    lon = data['longitude']
    return lat, lon


def get_map(lon, lat):
    url = "https://maps.googleapis.com/maps/api/staticmap?center=" + str(lon) + ', ' + str(lat) + \
          "&zoom=6&size=480x340&style=element:labels|visibility:off&style=element:geometry.stroke|visibility:off&style=feature:landscape|element:geometry|saturation:-100&style=feature:water|saturation:-100|invert_lightness:true&key=AIzaSyA2iEaDnCtneojYLIGs0oBdw40youqbMmY"
    return requests.get(url, stream=True).raw


# PREPARE THE BROWSER FOR USE
# LOADS DEFAULT HOME-PAGE
def prep_browser(url="https://www.google.com/"):
    return browser.get(url)


# CHECK IF ELEMENT EXISTS ON WEB PAGE
def is_element(id=None, name=None, xpath=None):
    try:
        if id is not None:
            return browser.find_element_by_id(id)
        elif name is not None:
            return browser.find_element_by_name(name)
        elif xpath is not None:
            return browser.find_element_by_xpath(xpath)
    except:
        # print('did not find', id, name, xpath, 'on', browser.current_url)
        return False


# CLOSE THE V.I. BROWSER
def close_browser():
    return browser.close()


# WEB SEARCH ---------------------------------------
# SEARCH THE WEB FOR A QUERY AND RETURN FIRST RESULT
def search(query, get_wiki=False, get_yt=False):

    if get_wiki and 'wiki' not in query:
        query = query + ' wikipedia'
    elif get_yt:
        prep_browser(url="https://www.youtube.com/")
        x = browser.find_element_by_name('search_query')
        x.clear()
        x.send_keys(query)
        x.submit()
        return

    prep_browser()

    search_box = browser.find_element_by_name('q')
    search_box.clear()
    search_box.send_keys(query)
    search_box.submit()

    try:
        links = browser.find_elements_by_xpath("//ol[@class'web_regular_results']//h3//a")
    except:
        links = browser.find_elements_by_xpath("//h3//a")

    result = []

    for link in links:
        href = link.get_attribute("href")
        result.append(href)

    if get_wiki:
        browser.get(result[0])
        r = browser.current_url
        if 'wiki' in str(r):
            return r.split(".org/wiki/")[1]
        else:
            return ''

    browser.get(result[0])
    r = tldextract.extract(browser.current_url)
    return r, browser.current_url


# NEWS SEARCH -:
# Returns trending news headlines
def get_news(keywords=None):

    # NEWS PARSING FUNCTION
    # RETURNS headline and keywords found within an article
    def parse(url):
        try:
            a = Article(url)
            a.download()
            a.parse()
            return remove_list(str(a.title), junkSpecials).replace(' s ', "'s "), \
                   a.keywords
        except Exception as e:
            print(e)
            return False

    # GET NEWS STORIES FROM A SOURCE
    # By default using new.google.com
    resp = urllib.request.urlopen("https://news.google.com/news/")
    soup = BeautifulSoup(resp, "lxml", from_encoding=resp.info().get_param('charset'))
    links = []

    # ADDS NEWS ARTICLES TO A LIST
    # Removes websites that are known to have anti-parsing techniques
    # Or just need a smarter V.I. to parse effectively.
    # Or requires a subscription to access
    for link in soup.find_all('a', href=True):
        l = link['href']
        if l.startswith('http') and l not in links and '.google' not in l\
                and '.youtube' not in l and '.blogger' not in l and '.blogspot' not in l \
                and not '.theguardian' in l and '.mirror' not in l and '.buzzfeed' not in l and \
                '.ft' not in l and '.npr' not in l and '.ny' not in l and '.latimes' not in l and \
                '.theaustralian' not in l and 'twitter.com/' not in l:
            links.append(l)
    result = []

    # CHECK EACH LINK IN LIST, REMOVES DUPLICATE STORIES
    # OR SELECTS STORIES WITH SPECIFIED KEYWORDS
    # Section has been reverted to an older state due to a code breaking bug.
    # Some functions may be missing
    collected = 0
    for x in range(len(links)) and collected < 5:
        try:
            parsed = parse(links[x])
            print('     ', collected, parsed)

            if parsed is False:
                print('     Failed to parse', links[x])
            else:
                if keywords is None:
                    result.append([parsed[0], links[x]])

                else:
                    for x2 in range(len(keywords)):

                        for x3 in range(len(parsed[1])):

                            if keywords[x2] == parsed[1][x3] or keywords[x2] in parsed[0]:
                                result.append([parsed[0], links[x]])
                                print('     web.get_news():', keywords[x], 'Found')

            print('     web.get_news():', x)
            collected = collected + 1

        except Exception as e:
            print('     web.get_news():', x, e)

    return result


# SEND EMAIL FUNCTION
# Server equals Gmail by default
def send_email(send_to, content):
    try:
        toaddrs = send_to
        msg = content
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(email_username, email_password)
        server.sendmail(email_username, toaddrs, msg)
        server.quit()
    except Exception as e:
        print('error', e)


def send_email_attach(file_name, file_path):
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    fromaddr = email_username
    toaddr = pushover_adr

    msg = MIMEMultipart()

    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = file_name

    import socket
    file_adr = str(socket.gethostbyname(socket.gethostname())) + ':8000'
    file_adr = file_adr + file_path.decode('utf-8').replace('C:', '')

    body = "Sharing File:\n" + str(file_adr)

    msg.attach(MIMEText(body, 'plain'))

    filename = file_name
    attachment = open(file_path, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, email_password)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


# FACEBOOK MESSENGER VAR
logged = False


# LOGIN TO FACEBOOK MESSENGER
def login_fbm():
    global logged, client
    try:
        client = Client(email=fb_email, password=fb_pass)
        logged = True
    except Exception as e:
        print('[ERROR] Failed to log into messenger\n'+str(e))
        logged = False


# SEND AN ACTION TO FACEBOOK MESSENGER:
# [FETCH] collects and returns the chat history
# [MARK] marks the last message as recieved & seen
# [SEND] sends a message given as parameter 'msg'
def action_fbm(action, user_id, msg='Hello.'):
    if logged:
        if action == 'fetch':
            client.friendConnect(user_id)
            return client.fetchThreadMessages(thread_id=user_id)[0].text
        elif action == 'mark':
            client.markAsDelivered(user_id, user_id)
            client.setTypingStatus(status=TypingStatus.TYPING, thread_id=user_id, thread_type=ThreadType.USER)
        elif action == 'send':
            sqlmem.query("UPDATE people "
                         "SET info='"+ object_string_converter(msg, in_type='string') + "' "
                         "WHERE uid='" + str(user_id) + "'")
            return client.send(Message(text=msg), thread_id=user_id, thread_type=ThreadType.USER)
        elif action == 'fetch_all':
            return client.fetchAllUsers()
    return


# LOGIN TO FACEBOOK in V.I. Browser
def login_fb():
    if logged:
        # Goto Facebook:
        browser.get('https://www.facebook.com/')
        # Check if logged in
        element = is_element(name='email')
        if element is not False:
            # Log in
            element.clear()
            element.send_keys(fb_email)
            element2 = is_element(name='pass')
            while element2 is False:
                element.submit()
                element2 = is_element(name='pass')
            element2.clear()
            element2.send_keys(fb_pass)
            element2.submit()


# CHECK FOR FRIEND REQUESTS
# Will either report to the user that a request has been recieved or automatically accept all requests
def fetch_requests_fbm():
    if logged:
        try:
            login_fb() # LOGIN TO FACEBOOK within Browser
            browser.get('https://www.facebook.com/friends/requests/?fcref=jwl')
            #browser.save_screenshot("./browser_report.png")
            element = browser.find_element_by_xpath('//*[@id="u_0_1s"]')
            element.click()
            # Saves a screen shot of open requests to the local dir
            #browser.save_screenshot("./browser_report2.png")
        except Exception as e:
            print(e)


# FETCH DATA FROM FITBIT WEB-API
# retrieves information from the user fitbit account
def get_fitbit(token, fit_id, stat=''):
    try:
        if stat == 'heart':
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/activities/heart/date/today/1d.json'
        elif stat == 'weight':
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/body/log/weight/date/today.json'
        elif stat == 'step':
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/activities/steps/date/today/1m.json'
        elif stat == 'sleep':
            url = 'https://api.fitbit.com/1.2/user/' + fit_id + '/sleep/date/today.json'
        elif stat == 'device':
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/devices.json'
        elif stat == 'calories':
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/activities/calories/date/today/1d.json'
        elif stat == 'bmi':
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/body/bmi/date/today/1d.json'
        else:
            url = 'https://api.fitbit.com/1/user/' + fit_id + '/profile.json'
        response = requests.get(url=url, headers={'Authorization': 'Bearer ' + token})
        return response.content
    except Exception as e:
        print(e)
        return False


# SET PUSHOVER ADR
def set_pushover_adr(new_adr):
    global pushover_adr
    pushover_adr = new_adr
    return


# SET FACEBOOK USER/PASS
def set_facebook(new_user, new_pass):
    global fb_email, fb_pass
    fb_email = new_user
    fb_pass = new_pass
    return login_fbm()


# SEND A PUSH NOTIFICATION via Best Option
def push_notify(contents, uid=0, notify=pushover_adr):
    if logged and uid > 0:
        return action_fbm('send', uid, msg=contents)

    elif not pushover_adr == '':
        return send_email(send_to=notify, content=contents)

    return 'No notification option avalible.'


# GET PHONETICS
def get_phonetics(string):
    prep_browser(url="https://tophonetics.com/")
    if is_element(id="text_to_transcribe"):
        q = browser.find_element_by_id('text_to_transcribe')
        q.clear()
        q.send_keys(string)
        q.submit()

        if is_element(id="submit"):
            q = browser.find_element_by_id('submit')
            q.click()

            if is_element(id="transcr_output"):
                q = browser.find_element_by_id('transcr_output')
                return str(q.text).encode('utf-8')

    return ''


# CHECK THE LATEST VERSION ON GIT
def git_update(my_version):
    prep_browser(url="https://github.com/Oweneaster/vi4-update-repo")

    if is_element(id="readme"):
        i = browser.find_element_by_id("readme")
        i = i.text.split('\n')

        if i[0] == 'README.md':
            i = int(i[1].split('[')[1].split(']')[0])

            if i > int(my_version):
                files = browser.find_elements_by_class_name("js-navigation-open")

                for file in files:
                    if file.text.endswith(".py"):

                        # GET file name
                        f_name = file.text.\
                            replace('sqlmem.py', 'data/sqlmem.py').\
                            replace('liteCore.py', 'data/liteCore.py').\
                            replace('osf.py', 'interface/osf.py').\
                            replace('web.py', 'interface/web.py').\
                            replace('Dictionary.py', 'lang/Dictionary.py').\
                            replace('langModule.py', 'lang/langModule.py')

                        # GET file download link
                        f_link = file.get_attribute("href").\
                            replace('github.com', 'raw.github.com').\
                            replace('/blob/master/', '/master/')

                        # DOWNLOAD FILE & UPDATE
                        print("Downloading", f_name, f_link)
                        urllib.request.urlretrieve(url=f_link, filename=f_name)

                return True

    return False


def financial_summary(username, password, pass_phrase, bank='bos'):
    if bank == 'bos':
        home = "https://online.bankofscotland.co.uk/personal/logon/login.jsp"
        browser.get(home)
        print('Logging onto: BOS')
        print('     USER_ID >> ', username)
        log = is_element(id="frmLogin:strCustomerLogin_userID")
        log.click(), log.clear(), log.send_keys(username)
        print('     CHECK')
        browser.implicitly_wait(time_to_wait=1)
        print('     USER_PS >> ', password)
        log = is_element(id="frmLogin:strCustomerLogin_pwd")
        log.click(), log.clear(), log.send_keys(password)
        print('     CHECK')
        browser.implicitly_wait(time_to_wait=2)
        if browser.current_url == home:
            try:
                log = browser.find_element_by_id("frmLogin:btnLogin2")
                log.click()
            except Exception as e:
                print('     FAILED:', e)
        else:
            print(browser.current_url, home)
        browser.implicitly_wait(time_to_wait=3)
        if not browser.current_url == home:
            print('     SUCCESS!')
        browser.save_screenshot("./bos2.png")
financial_summary(username='OWENCEASTER', password='mid7night', pass_phrase='')


def forecast_summary():
    try:
        browser.get('https://www.bbc.co.uk/weather/2649183')
        forecasts = browser.find_element_by_xpath('//*[@id="wr-o-tabset__title--today"]')
        forecasts.click()
        forecasts = browser.find_elements_by_class_name('wr-c-text-forecast__summary-text')
        for forecast in forecasts:
            if not forecast.text == '':
                f = forecast.text
    except: pass

    try:
        forecasts = browser.find_element_by_xpath('//*[@id="wr-o-tabset__title--tomorrow"]')
        forecasts.click()
        forecasts = browser.find_elements_by_class_name('wr-c-text-forecast__summary-text')
        for forecast in forecasts:
            if not forecast.text == '':
                f = f + '\n' + forecast.text
    except: pass

    return f


def get_easy_recipe():
    browser.get("http://allrecipes.co.uk/recipes/tag-361/quick-and-easy-recipes.aspx")
    if is_element(xpath='//*[@id="consentButtonContainer"]/button'):
        r = browser.find_element_by_xpath('//*[@id="consentButtonContainer"]/button')
        r.click()
    if is_element(id='recipeSpinnerButton'):
        r = browser.find_element_by_id('recipeSpinnerButton')
        r.click()
        time.sleep(5)
    if is_element(xpath='//*[@id="recipeSpinnerSelected"]'):
        r = browser.find_element_by_xpath('//*[@id="recipeSpinnerSelected"]')
        return r.text, r.get_attribute('href')
    return '', ''


# END OF FILE [web.py]
