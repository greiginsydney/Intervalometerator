# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# This script is part of the Intervalometerator project, a time-lapse camera controller for DSLRs:
# https://github.com/greiginsydney/Intervalometerator
# https://greiginsydney.com/intvlm8r
# https://intvlm8r.com
#
# This script incorporates code from python-gphoto2, and we are incredibly indebted to Jim Easterbrook for it.
# python-gphoto2 - Python interface to libgphoto2 http://github.com/jim-easterbrook/python-gphoto2 Copyright (C) 2015-17 Jim
# Easterbrook jim@jim-easterbrook.me.uk



from datetime import timedelta, datetime
from decimal import Decimal     # Thumbs exposure time calculations
#from PIL import Image           # For the camera page preview button
from urllib.parse import urlparse, urljoin
import calendar
import configparser             # For the ini file (used by the Transfer page)
import exifreader               # For thumbnails
import imageio                  # Thumbnails & the camera page preview button
import fnmatch                  # Used for testing filenames
import importlib.util           # Testing installed packages
import io                       # Camera preview
import json
import logging
import os                       # Hostname
import psutil
import rawpy                    # Thumbnails
import re                       # RegEx. Used in Copy Files & createDestFilename
from smbus2 import SMBus        # For I2C
import struct
import subprocess
import sys
import time

import gphoto2 as gp

from cachelib import SimpleCache
cache = SimpleCache()

from werkzeug.security import check_password_hash

from flask import Flask, flash, render_template, request, redirect, url_for, make_response, abort, jsonify, g
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin, login_url
from celery import Celery, chain
from celery.app.control import Inspect

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

app.secret_key = b'### Paste the secret key here. See the Setup docs ###' #Cookie for session messages
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['result_backend'])
celery.conf.update(app.config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = ''

#Deep gphoto logging enabled when debugging:
callback_obj = gp.check_result(gp.use_python_logging(mapping={
    gp.GP_LOG_ERROR   : logging.INFO,
    gp.GP_LOG_DEBUG   : logging.DEBUG,
    gp.GP_LOG_VERBOSE : logging.DEBUG - 3,
    gp.GP_LOG_DATA    : logging.DEBUG - 6}))

# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

PI_PHOTO_DIR  = os.path.expanduser('/home/pi/photos')
PI_THUMBS_DIR = os.path.expanduser('/home/pi/thumbs')
PI_THUMBS_INFO_FILE = os.path.join(PI_THUMBS_DIR, 'piThumbsInfo.txt')
PI_PREVIEW_DIR = os.path.expanduser('/home/pi/preview')
PI_PREVIEW_FILE = 'intvlm8r-preview.jpg'
PI_TRANSFER_DIR = os.path.expanduser('/home/pi/www/static')
PI_TRANSFER_FILE = os.path.join(PI_TRANSFER_DIR, 'piTransfer.log')
PI_TRANSFER_LINK = 'static/piTransfer.log' #This is the file that the Transfer page will link to when you click "View Log"
gunicorn_logger = logging.getLogger('gunicorn.error')
REBOOT_SAFE_WORD = 'sayonara'
HOSTNAME = os.uname()[1]
RAWEXTENSIONS = ('.CR2', '.NEF')

# Our user database:
#users = {'admin': {'password': '### Paste the hash of the password here. See the Setup docs ###'}}
users = {'admin': {'password': 'password'}}
#users.update({'superuser': {'password': 'godmode'}}) #Un-comment, copy and update this line as required to add more user logins

app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

bus = SMBus(1) #Initalise the I2C bus
# This is the address we setup in the Arduino Program
address = 0x04

iniFile = os.path.join(app.root_path, 'intvlm8r.ini')

arduinoDoW = ["Unknown", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

cameraPreviewBlocklist = [""]

#Suppress the display of any uninstalled transfer options:
hiddenTransferOptions = ''
hiddenTransferDict = {
  "paramiko": "SFTP",
  "dropbox": "Dropbox",
  "google": "Google Drive"
}
# TY SO: https://stackoverflow.com/a/41815890
for package_name in ('paramiko', 'dropbox', 'google'):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        app.logger.debug(package_name + ' is not installed')
        hiddenTransferOptions = hiddenTransferOptions + "," + hiddenTransferDict[package_name]
app.logger.debug('hiddenTransferOptions = ' + hiddenTransferOptions)

def writeString(value):
    ascii = [ord(c) for c in value]
    for x in range(0, 2):
        try:
            bus.write_i2c_block_data(address, 0, ascii)
        except Exception as e:
            app.logger.debug('writeString error: ' + str(e))
            time.sleep(1) # Wait a second before each retry
    time.sleep(0.5) # Give the Arduino time to act on the data sent
    return -1


def readString(value):
    status = ""
    ascii = ord(value[0])
    app.logger.debug('ASCII = ' + str(ascii))
    rxLength = 32
    if (ascii == 48 ): rxLength = 8  # "0" - Date - 8
    if (ascii == 49 ): rxLength = 8  # "1" - Time
    if (ascii == 50 ): rxLength = 11 # "2" - Last/next shots
    if (ascii == 51 ): rxLength = 7  # "3" - Interval
    # if (ascii == 52 ): rxLength = 7  # "4" - All temps (current, max, min)
    # if (ascii == 53 ): rxLength = 4  # "5" - WakePi hour and runtime

    for x in range(0, 2):
        try:
            array = bus.read_i2c_block_data(address, ascii, rxLength)
            for i in range(len(array)):
                 if (array[i] == 0):
                     break
                 status += chr(array[i])
            app.logger.debug('Status received was: >' + status + "<")
            break
        except Exception as e:
            app.logger.debug('readString error: ' + str(e))
            time.sleep(1) # Wait a second before each retry
    if status == "":
        status = "Unknown"
    return status


def getPiUptime():
    uptime_string = "Unknown"
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = str(timedelta(seconds = round(uptime_seconds)))
    except:
        pass
    return uptime_string


def getPiTemp():
    temp = "Unknown"
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as tempfile:
            temp = '{0:.0f}'.format(round(int(tempfile.read()) / 1000, 0))
    except Exception as e:
        app.logger.debug('Pi temp error: ' + str(e))
    app.logger.debug('Pi temp = ' + temp)
    return temp


@app.context_processor
def customisation():
    loc = cache.get('locationName')
    if loc is None:
        #The cache is empty? Read the location from the Ini file
        loc = getIni('Global', 'locationName', 'string', 'Intvlm8r')
        cache.set('locationName', loc, timeout = 0)
    return dict (locationName = loc )


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return
    user = User()
    user.id = username
    return user


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return
    user = User()
    user.id = username
    return user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        app.logger.debug("It's a GET to LOGIN")
        return render_template('login.html')
    username = (str(request.form['username']))
    remember = 'false'
    for name, _ in users.items():
        if (username.casefold() == name.casefold()):
            #OK, we have the user name (regardless of the case)!
            if users[name]['password'] == request.form['password']:
            #if (check_password_hash(users[username]['password'], request.form['password'])):
                user = User()
                user.id = name
                if request.form.get('rememberme'):
                    remember = 'true'
                login_user(user,'remember=' + remember)
                app.logger.debug('Logged-in ' + name)
                next = request.args.get('next')
                # is_safe_url should check if the url is safe for redirects.
                # See http://flask.pocoo.org/snippets/62/ for an example.
                if not is_safe_url(next):
                    return abort(400)
                return redirect(next or url_for('main'))
    app.logger.debug('User \'' + username + '\' failed to login')
    flash('Bad creds. Try again')
    return redirect(url_for('login'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('login'))


@login_manager.unauthorized_handler
def unauthorized_handler():
    flash('You need to log in before you can access that page!')
    return redirect(login_url(url_for('login'), request.url))


@app.route("/")
@login_required
def main():
    templateData = {
        'arduinoDate'       : 'Unknown',
        'arduinoTime'       : '',
        'arduinoLastShot'   : 'Unknown',
        'arduinoNextShot'   : 'Unknown',
        'cameraBattery'     : 'Unknown',
        'fileCount'         : 'Unknown',
        'lastImage'         : 'Unknown',
        'availableShots'    : 'Unknown',
        'cameraDaysFree'    : 'Unknown',
        'piInterval'        : '',
        'piImageCount'      : 'Unknown',
        'piLastImage'       : 'Unknown',
        'piSpaceFree'       : 'Unknown',
        'piDaysFree'        : 'Unknown',
        'daysFreeWarn'      : '0',
        'daysFreeAlarm'     : '0',
        'lastTrnResult'     : 'Unknown',
        'lastTrnLogFile'    : PI_TRANSFER_LINK,
        'piLastImageFile'   : 'Unknown'
    }

    app.logger.debug('YES - this bit of MAIN fired!')

    args = request.args.to_dict()
    if args.get('wakeCamera'):
        writeString("WC") # Sends the WAKE command to the Arduino
        time.sleep(1);    # (Adds another second on top of the 0.5s baked into WriteString)
        app.logger.debug('Returned after detecting camera wake command')
        return redirect(url_for('main'))

    templateData['arduinoDate'] = getArduinoDate() # Failure returns "Unknown"
    templateData['arduinoTime'] = getArduinoTime() # Failure returns ""

    try:
        arduinoStats = str(readString("2"))
        if arduinoStats != "Unknown":
            lastShot= arduinoStats.split(":")[0]
            if lastShot != "19999":
                templateData['arduinoLastShot'] = arduinoDoW[int(lastShot[0:1])] + " " + lastShot[1:3]+ ":" + lastShot[3:5]
            nextShot = arduinoStats.split(":")[1]
            if nextShot != "19999":
                templateData['arduinoNextShot'] = arduinoDoW[int(nextShot[0:1])] + " " + nextShot[1:3]+ ":" + nextShot[3:5]
    except:
        pass
    #except Exception as e:
    #    app.logger.debug('Time template error: ' + str(e))

    # Camera comms:
    try:
        camera, context, config = connectCamera()
        if camera:
            storage_info = gp.check_result(gp.gp_camera_get_storageinfo(camera))
            if len(storage_info) == 0:
                flash('No storage info available') # The memory card is missing or faulty
            files = list_camera_files(camera)
            if not files:
                fileCount = 0
                lastImage = 'n/a'
            else:
                fileCount = len(files)
                info = get_camera_file_info(camera, files[-1]) #Get the last file
                lastImage = datetime.utcfromtimestamp(info.file.mtime).isoformat(' ')
            gp.check_result(gp.gp_camera_exit(camera))
            templateData['fileCount']                = fileCount
            templateData['lastImage']                = lastImage
            templateData['cameraBattery'], discardMe = readRange (camera, context, 'status', 'batterylevel')

            #Find the capturetarget config item. (TY Jim.)
            capture_target = gp.check_result(gp.gp_widget_get_child_by_name(config, 'capturetarget'))
            currentTarget = gp.check_result(gp.gp_widget_get_value(capture_target))
            #app.logger.debug('Current captureTarget =  ' + str(currentTarget))
            if currentTarget == "Internal RAM":
                #Change it to "Memory Card"
                try:
                    newTarget = 1
                    newTarget = gp.check_result(gp.gp_widget_get_choice(capture_target, newTarget))
                    gp.check_result(gp.gp_widget_set_value(capture_target, newTarget))
                    gp.check_result(gp.gp_camera_set_config(camera, config))
                    config = camera.get_config(context) #Refresh the config data for the availableshots to be read below
                    app.logger.debug('Set captureTarget to "Memory Card" in main')
                except gp.GPhoto2Error as e:
                    app.logger.debug('GPhoto camera error setting capturetarget in main: ' + str(e))
                except Exception as e:
                    app.logger.debug('Unknown camera error setting capturetarget in main: ' + str(e))
            templateData['availableShots'] = readValue (config, 'availableshots')
            gp.check_result(gp.gp_camera_exit(camera))
    except Exception as e:
        app.logger.debug('Unknown camera error in main: ' + str(e))

    # Pi comms:
    piLastImage = ''
    piLastImageFile = ''
    try:
        FileList = list_Pi_Images(PI_PHOTO_DIR)
        PI_PHOTO_COUNT = len(FileList)
        if PI_PHOTO_COUNT >= 1:
            FileList.sort(key=lambda x: os.path.getmtime(x))
            piLastImage = datetime.utcfromtimestamp(os.path.getmtime(FileList[-1])).replace(microsecond=0)
            piLastImageFile = str(FileList[-1])
            #This code replaces a RAW image on the main page with its .JPG twin - if one exists. (You're shooting in RAW+JPG mode)
            if piLastImageFile.endswith(RAWEXTENSIONS):
                piLastImageFileAsJpg = piLastImageFile.replace(".CR2", ".JPG")
                piLastImageFileAsJpg = piLastImageFileAsJpg.replace(".NEF", ".JPG")
                if os.path.exists(piLastImageFileAsJpg):
                    piLastImageFile = piLastImageFileAsJpg
                    piLastImageFile = 'photos/' + piLastImageFile.replace((PI_PHOTO_DIR  + "/"), "")      #Fix the path
                else:
                    piLastImageFile = 'thumbs/' + piLastImageFileAsJpg.replace((PI_PHOTO_DIR  + "/"), "") #Fix the path
                    piLastImageFile = piLastImageFile.replace((".JPG"), "-thumb.JPG")                     #Add the '-thumb' suffix
            else:
                piLastImageFile = 'photos/' + piLastImageFile.replace((PI_PHOTO_DIR  + "/"), "")
    except:
        flash('Error talking to the Pi')
        PI_PHOTO_COUNT = 0
    templateData['piLastImageFile'] = piLastImageFile
    templateData['piImageCount']    = PI_PHOTO_COUNT
    templateData['piLastImage']     = piLastImage
    templateData['piSpaceFree'],piBytesFree = getDiskSpace()
    largestImageSize = getLargestImageSize(PI_PHOTO_DIR)
    shotsPerDay = getShotsPerDay()
    #Python rounds up, which I don't want. This "- 0.5" is also to align with the same result calculated by Javascript on the /intervalometer page.
    try:
        templateData['piDaysFree'] = str(round(((piBytesFree / largestImageSize) / shotsPerDay) - 0.5))
    except:
        None
    try:
        templateData['cameraDaysFree'] = round((int(templateData['availableShots']) / shotsPerDay) - 0.5)
    except:
        None
    templateData['daysFreeWarn']  = int(getIni('Thresholds', 'daysfreewarn', 'int', '14'))
    templateData['daysFreeAlarm']  = int(getIni('Thresholds', 'daysfreealarm', 'int', '7'))
    
    try:
        with open(PI_TRANSFER_FILE, 'r') as f:
            for line in reversed(f.read().splitlines()):
                if 'STATUS: ' in line:
                    templateData['lastTrnResult'] = line.replace('STATUS: ','')
                    break
    except Exception as e:
        app.logger.debug('Exception reading STATUS in piTransfer.log file: ' + str(e))
    return render_template('main.html', **templateData)


@app.route("/getTime")
def getTime():
    """
    This 'page' is only one of three called without the "@login_required" decorator. It's only called by
    the cron job/ setTime.py script and will only execute if the calling IP is itself/localhost.
    """
    sourceIp = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if sourceIp != "127.0.0.1":
        abort(403)
    arduinoDate = getArduinoDate()
    arduinoTime = getArduinoTime()
    res = make_response('<div id="dateTime">' + arduinoDate + ' ' + arduinoTime + '</div>')
    return res, 200


@app.route("/setArduinoDateTime")
def setArduinoDateTime():
    """
    This 'page' is only one of three called without the "@login_required" decorator. It's only called by
    the cron job/ setTime.py script and will only execute if the calling IP is itself/localhost.
    """
    sourceIp = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if sourceIp != "127.0.0.1":
        abort(403)

    newTime = datetime.now().strftime('%Y%m%d%H%M%S') #20190613235900
    writeString("ST=" + newTime) # Send the new time and date to the Arduino
    app.logger.debug('setArduinoDateTime to {0}'.format(newTime))
    res = make_response('<p>Set Arduino datetime to ' + newTime + '</p>')
    return res, 200


def getArduinoDate():
    formattedDate = 'Unknown'
    try:
        rawDate = str(readString("0"))
        if rawDate != 'Unknown':
            formattedDate = datetime.strptime(rawDate, '%Y%m%d').strftime('%Y %b %d')
        time.sleep(0.5);
    except:
        pass
    return formattedDate


def getArduinoTime():
    formattedTime = ''
    try:
        rawTime = str(readString("1"))
        if rawTime != 'Unknown':
            formattedTime = rawTime[0:2] + ":" + rawTime[2:4] + ":" + rawTime[4:6]
        time.sleep(0.5);
    except:
        pass
    return formattedTime


@app.route("/thumbnails")
@login_required
def thumbnails():
    """
    The logic here warrants some explanation: It's *assumed* that for every photo on the Pi there's a matching thumbnail, as the
    copy and thumb creation process are linked. You *shouldn't* have one without the other.
    This code creates the thumbnails list based on the filename of the main image, and then only adds the assumed -thumbs.JPG suffix as it calls the view.
    Thus, even if a thumb is absent (broken?), the view will still reveal its main image, the image's metadata, and you can still click-through to see it.

    Had I started with "list_Pi_Images(PI_THUMBS_DIR)", then a missing thumb would result in its main image not being displayed here.
    """
    ThumbFiles = []
    ThumbsToShow = int(getIni('Global', 'thumbsCount', 'int', '24'))

    try:
        FileList  = list_Pi_Images(PI_PHOTO_DIR)
        PI_PHOTO_COUNT = len(FileList)
        if PI_PHOTO_COUNT >= 1:
            FileList.sort(key=lambda x: os.path.getmtime(x))
            ThumbnailCount = min(ThumbsToShow,PI_PHOTO_COUNT) # The lesser of these two values
            #Read all the thumb exifData ready to create the page:
            ThumbsInfo = {}
            if os.path.exists(PI_THUMBS_INFO_FILE):
                with open(PI_THUMBS_INFO_FILE, 'rt') as f:
                    for line in f:
                        if ' = ' in line:
                            try:
                                (key, val) = line.rstrip('\n').split(' = ')
                                ThumbsInfo[key] = val
                            except Exception as e:
                                #Skip over bad line
                                app.logger.debug('Error in thumbs info file: ' + str(e))
            #Read the thumb files themselves:
            for loop in range(-1, (-1 * (ThumbnailCount + 1)), -1):
                _, imageFileName = os.path.split(FileList[loop])
                #Read the exifData:
                thumbTimeStamp = 'Unknown'
                thumbInfo = 'Unknown'
                exifData = ThumbsInfo.get(imageFileName)
                #app.logger.debug(str(exifData))
                if exifData != None:
                    thumbTimeStamp = exifData.split("|")[0]
                    thumbInfo = exifData.split("|")[1]
                #Build the list for the page:
                ThumbFileName = createDestFilename(FileList[loop], PI_THUMBS_DIR, '-thumb')
                ThumbFiles.append({'Name': (str(ThumbFileName).replace((PI_THUMBS_DIR  + "/"), "")), 'TimeStamp': thumbTimeStamp, 'Info': thumbInfo })
        else:
            flash("There are no images on the Pi. Copy some from the Transfer page.")
    except Exception as e:
        app.logger.debug('Thumbs error: ' + str(e))
    return render_template('thumbnails.html', ThumbFiles = ThumbFiles)


@app.route("/camera")
@login_required
def camera():
    cameraData = {
        'cameraModel'   : '',
        'cameraLens'    : 'Unknown',
        'cameraDate'    : '',
        'focusmode'     : '',
        'exposuremode'  : '',
        'autopoweroff'  : '',
        'imgfmtselected': '',
        'imgfmtoptions' : '',
        'wbselected'    : '',
        'wboptions'     : '',
        'isoselected'   : '',
        'isooptions'    : '',
        'apselected'    : '',
        'apoptions'     : '',
        'shutselected'  : '',
        'shutoptions'   : '',
        'expselected'   : '',
        'expoptions'    : '',
        'piPreviewFile' : '',
        'cameraMfr'     : 'Unknown',
        'blockPreview'  : 'False'
        }

    args = request.args.to_dict()
    if args.get('preview'):
        cameraData['piPreviewFile'] = PI_PREVIEW_FILE + '?' + str(calendar.timegm(time.gmtime())) #Adds a unique suffix so the browser always downloads the file

    if args.get('wakeCamera'):
        writeString("WC") # Sends the WAKE command to the Arduino
        time.sleep(1);    # (Adds another second on top of the 0.5s baked into WriteString)
        app.logger.debug('Returned after detecting camera wake command')
        return redirect(url_for('camera'))

    try:
        camera, context, config = connectCamera()
        if camera:
            abilities = gp.check_result(gp.gp_camera_get_abilities(camera))
            cameraData['cameraModel']              = abilities.model
            cameraData['cameraLens'], discardMe    = readRange (camera, context, 'status', 'lensname')
            if (cameraData['cameraLens'] == 'Unknown'):
                #Try to build this from focal length:
                focalMin, discardMe = readRange (camera, context, 'status', 'minfocallength')
                focalMax, discardMe = readRange (camera, context, 'status', 'maxfocallength')
                if (focalMin == focalMax):
                    cameraData['cameraLens'] = focalMin
                else:
                    focalMin = focalMin.replace(" mm", "")
                    cameraData['cameraLens'] = ('{0}-{1}'.format(focalMin,focalMax))
            cameraTimeAndDate = getCameraTimeAndDate(camera, context, config, 'Unknown')
            cameraMfr, discardMe = readRange (camera, context, 'status', 'manufacturer')
            if 'Nikon' in cameraMfr:
                cameraMfr = 'Nikon'
                cameraData['cameraMfr'] = 'Nikon'
            elif 'Canon' in cameraMfr:
                cameraMfr = 'Canon'
                cameraData['cameraMfr'] = 'Canon'
            if (cameraMfr == 'Nikon'):
                imgfmtselected, imgfmtoptions   = readRange (camera, context, 'capturesettings', 'imagequality')
                apselected, apoptions           = readRange (camera, context, 'capturesettings', 'f-number')
                cameraData['exposuremode']      = readValue (config, 'expprogram')
            else:
                imgfmtselected, imgfmtoptions   = readRange (camera, context, 'imgsettings', 'imageformat')
                apselected, apoptions           = readRange (camera, context, 'capturesettings', 'aperture')
                cameraData['exposuremode']      = readValue (config, 'autoexposuremode')
            #Attributes generic to all cameras:
            wbselected, wboptions           = readRange (camera, context, 'imgsettings', 'whitebalance')
            isoselected, isooptions         = readRange (camera, context, 'imgsettings', 'iso')
            shutselected, shutoptions       = readRange (camera, context, 'capturesettings', 'shutterspeed')
            expselected, expoptions         = readRange (camera, context, 'capturesettings', 'exposurecompensation')

            abilities = gp.check_result(gp.gp_camera_get_abilities(camera))
            if abilities.model in cameraPreviewBlocklist:
                cameraData['blockPreview']  = 'True'
                
            gp.check_result(gp.gp_camera_exit(camera))
            cameraData['cameraDate']    = cameraTimeAndDate
            cameraData['focusmode']     = readValue (config, 'focusmode')
            cameraData['exposuremode']  = readValue (config, 'autoexposuremode')
            if (cameraData['exposuremode'] == "Not available"):
                #try "expprogram"
                cameraData['exposuremode']  = readValue (config, 'expprogram')
            cameraData['autopoweroff']  = readValue (config, 'autopoweroff')
            cameraData['imgfmtselected']= imgfmtselected
            cameraData['imgfmtoptions'] = imgfmtoptions
            cameraData['wbselected']    = wbselected
            cameraData['wboptions']     = wboptions
            cameraData['isoselected']   = isoselected
            cameraData['isooptions']    = isooptions
            cameraData['apselected']    = apselected
            cameraData['apoptions']     = apoptions
            cameraData['shutselected']  = shutselected
            cameraData['shutoptions']   = shutoptions
            cameraData['expselected']   = expselected
            cameraData['expoptions']    = expoptions
    except Exception as e:
        app.logger.debug('Unknown camera GET error: ' + str(e))

    templateData = cameraData.copy()
    return render_template('camera.html', **templateData)


@app.route("/camera", methods = ['POST'])    # The camera's POST method
@login_required
def cameraPOST():
    """ This page is where you manage all the camera settings."""
    preview = None
    try:
        camera, context, config = connectCamera()
        if camera:
            if request.form['CamSubmit'] == 'apply':
                app.logger.debug('-- Camera Apply selected')
                cameraMfr = request.form.get('cameraMfr')
                app.logger.debug('cameraMfr = {0}'.format(cameraMfr))
                if cameraMfr == 'Canon':
                    #This *does* write a new setting to the camera:
                    node = config.get_child_by_name('imageformat') #
                    node.set_value(str(request.form.get('img')))
                    if (request.form.get('aperture') != None):
                        node = config.get_child_by_name('aperture')
                        node.set_value(str(request.form.get('aperture')))
                elif cameraMfr == 'Nikon':
                    #This *does* write a new setting to the camera:
                    node = config.get_child_by_name('imagequality') #
                    node.set_value(str(request.form.get('img')))
                    if (request.form.get('aperture') != None):
                        node = config.get_child_by_name('f-number')
                        node.set_value(str(request.form.get('aperture')))
                else:
                    pass
                # Don't bother sending any of the "read only" settings:
                if (request.form.get('wb') != None):
                    node = config.get_child_by_name('whitebalance')
                    node.set_value(str(request.form.get('wb')))
                if (request.form.get('iso') != None):
                    node = config.get_child_by_name('iso')
                    node.set_value(str(request.form.get('iso')))
                if (request.form.get('shutter') != None):
                    node = config.get_child_by_name('shutterspeed')
                    node.set_value(str(request.form.get('shutter')))
                if (request.form.get('exp') != None):
                    node = config.get_child_by_name('exposurecompensation')
                    node.set_value(str(request.form.get('exp')))
                camera.set_config(config, context)
                gp.check_result(gp.gp_camera_exit(camera))

            if request.form['CamSubmit'] == 'preview':
                app.logger.debug('-- Camera Preview selected')
                getPreviewImage(camera, context, config)
                gp.check_result(gp.gp_camera_exit(camera))
                preview = 1
    except Exception as e:
        app.logger.debug('Unknown camera POST error: ' + str(e))

    return redirect(url_for('camera', preview = preview))


@app.route("/intervalometer")
@login_required
def intervalometer():
    """ This page is where you manage all the interval settings for the Arduino."""

    templateData = {
        'piDoW'            : '',
        'piStartHour'      : '',
        'piEndHour'        : '',
        'piInterval'       : '',
        'availableShots'   : 'Unknown',
        'piAvailableShots' : 'Unknown',
        'daysFreeWarn'     : '0',
        'daysFreeAlarm'    : '0'
    }
    app.logger.debug('This is a GET to Intervalometer')

    # Camera comms:
    try:
        camera, context, config = connectCamera()
        if camera:
            #Find the capturetarget config item. (TY Jim.)
            capture_target = gp.check_result(gp.gp_widget_get_child_by_name(config, 'capturetarget'))
            currentTarget = gp.check_result(gp.gp_widget_get_value(capture_target))
            #app.logger.debug('Current captureTarget =  ' + str(currentTarget))
            if currentTarget == "Internal RAM":
                #Change it to "Memory Card"
                try:
                    newTarget = 1
                    newTarget = gp.check_result(gp.gp_widget_get_choice(capture_target, newTarget))
                    gp.check_result(gp.gp_widget_set_value(capture_target, newTarget))
                    gp.check_result(gp.gp_camera_set_config(camera, config))
                    config = camera.get_config(context) #Refresh the config data for the availableshots to be read below
                    app.logger.debug('Set captureTarget to "Memory Card" in /intervalometer')
                except gp.GPhoto2Error as e:
                    app.logger.debug('GPhoto camera error setting capturetarget in /intervalometer: ' + str(e))
                except Exception as e:
                    app.logger.debug('Unknown camera error setting capturetarget in /intervalometer: ' + str(e))
            templateData['availableShots'] = readValue (config, 'availableshots')
            gp.check_result(gp.gp_camera_exit(camera))
    except Exception as e:
        app.logger.debug('Unknown camera error in intervalometer: ' + str(e))

    ArdInterval = str(readString("3"))
    #Returns a string that's <DAY> (a byte to be treated as a bit array of days) followed by 2-digit strings of <startHour>, <endHour> & <Interval>:
    app.logger.debug('Int query returned: ' + ArdInterval)
    if (ArdInterval != "Unknown") & (len(ArdInterval) == 7):
        for bit in range(1,8): # i.e. 1-7 inclusive
            if (ord(ArdInterval[0]) & (0b00000001<<bit)):
                app.logger.debug('Added ' + arduinoDoW[bit])
                templateData['piDoW'] += arduinoDoW[bit]   #Crude but effective: no need for csv niceties with this one
        templateData['piStartHour'] = ArdInterval[1:3]
        templateData['piEndHour'] = ArdInterval[3:5]
        templateData['piInterval'] = ArdInterval[5:7]
        app.logger.debug('Decoded Interval = ' + ArdInterval[5:7])
    
    _,piBytesFree = getDiskSpace()
    largestImageSize = getLargestImageSize(PI_PHOTO_DIR)
    templateData['piAvailableShots'] = str(round(piBytesFree / largestImageSize))
    templateData['daysFreeWarn']  = int(getIni('Thresholds', 'daysfreewarn', 'int', '14'))
    templateData['daysFreeAlarm']  = int(getIni('Thresholds', 'daysfreealarm', 'int', '7'))
    
    return render_template('intervalometer.html', **templateData)


@app.route("/intervalometer", methods = ['POST'])    # The intervalometer's POST method
@login_required
def intervalometerPOST():
    """ This page is where you manage all the interval settings for the Arduino."""
    newInterval = ""
    shootDays = 0
    shootDaysList = request.form.getlist('shootDays')
    startHour = str(request.form.get('startHour'))
    endHour   = str(request.form.get('endHour'))
    interval  = '{:0>2}'.format(str(request.form.get('interval'))) #"Padright" : https://docs.python.org/2/library/string.html#formatstrings

    if (len(shootDaysList) != 0) & (startHour != 'None') & (endHour != 'None') & (interval != 'None'):
        for day in shootDaysList:
            bit = (time.strptime(day, "%A").tm_wday) + 2
            if (bit >= 8):
                bit = 1   #Correct for Python days starting with Monday = 0
            shootDays |= (1<<bit)   #Set the bit that corresponds to the named weekday
        app.logger.debug('Shoot days =  {:b}'.format(shootDays))
        newInterval += chr(shootDays)
        newInterval += startHour
        newInterval += endHour
        newInterval += interval
        writeString("SI=" + str(newInterval)) # Send the new interval data to the Arduino
        app.logger.debug('Detected a valid POST. Updated the interval to ' + str(newInterval))
    else:
        app.logger.debug('Detected an *invalid* POST')
        flash('Invalid data posted to the page')
    return redirect(url_for('intervalometer'))


@app.route("/transfer")
@login_required
def transfer():
    """ This page is where you manage how the images make it from the camera to the real world."""

    if not os.path.exists(iniFile):
        createConfigFile(iniFile)
    # Initialise the dictionary:
    templateData = {
        'tfrMethod'             : 'Off',    # Hides all options if the file isn't found or is bad
        'ftpServer'             : '',
        'ftpUser'               : '',
        'ftpPassword'           : '',
        'ftpRemoteFolder'       : '',
        'sftpServer'            : '',
        'sftpUser'              : '',
        'sftpPassword'          : '',
        'sftpRemoteFolder'      : '',
        'googleRemoteFolder'    : '',
        'dbx_token'             : '',
        'transferDay'           : '',
        'transferHour'          : '',
        'copyDay'               : '',
        'copyHour'              : '',
        'wakePiTime'            : '25',
        'piTransferLogLink'     : PI_TRANSFER_LINK,
        'hiddenTransferOptions' : hiddenTransferOptions
    }
    config = configparser.ConfigParser(
        {
        'tfrmethod'          : 'Off',
        'ftpServer'          : '',
        'ftpUser'            : '',
        'ftpPassword'        : '',
        'ftpRemoteFolder'    : '',
        'sftpServer'         : '',
        'sftpUser'           : '',
        'sftpPassword'       : '',
        'sftpRemoteFolder'   : '',
        'googleRemoteFolder' : '',
        'dbx_token'          : '',
        'transferDay'        : '',
        'transferHour'       : '',
        'copyDay'            : 'Off',
        'copyHour'           : '',
        'wakePiTime'         : '25'
        })
    try:
        config.read(iniFile)
        #app.logger.debug('Found the file in GET')
        templateData['tfrMethod']          = config.get('Transfer', 'tfrmethod')
        templateData['ftpServer']          = config.get('Transfer', 'ftpServer')
        templateData['ftpUser']            = config.get('Transfer', 'ftpUser')
        templateData['ftpPassword']        = config.get('Transfer', 'ftpPassword')
        templateData['ftpRemoteFolder']    = config.get('Transfer', 'ftpRemoteFolder')
        templateData['sftpServer']         = config.get('Transfer', 'sftpServer')
        templateData['sftpUser']           = config.get('Transfer', 'sftpUser')
        templateData['sftpPassword']       = config.get('Transfer', 'sftpPassword')
        templateData['sftpRemoteFolder']   = config.get('Transfer', 'sftpRemoteFolder')
        templateData['googleRemoteFolder'] = config.get('Transfer', 'googleRemoteFolder')
        templateData['dbx_token']          = config.get('Transfer', 'dbx_token')
        templateData['transferDay']        = config.get('Transfer', 'transferDay')
        templateData['transferHour']       = config.get('Transfer', 'transferHour')
        templateData['copyDay']            = config.get('Copy', 'copyDay')
        templateData['copyHour']           = config.get('Copy', 'copyHour')
    except Exception as e:
        app.logger.debug('INI file error: ' + str(e))
        flash('Error reading from the Ini file')

    rawWakePi = str(readString("5"))
    if rawWakePi != "Unknown":
        templateData['wakePiTime']     = rawWakePi[0:2]

    return render_template('transfer.html', **templateData)


@app.route("/transfer", methods = ['POST'])    # The camera's POST method
@login_required
def transferPOST():
    """ This page is where you manage how the images make it from the camera to the real world."""

    if 'tfrClear' in request.form:
        try:
            piTransferLogfile = open(PI_TRANSFER_FILE, 'w')
            nowtime = datetime.now().strftime('%Y/%m/%d %H:%M:%S') #2019/09/08 13:06:03
            piTransferLogfile.write(nowtime + ' STATUS: piTransfer.log cleared\r\n')
            piTransferLogfile.close()
        except Exception as e:
            app.logger.debug('Exception clearing piTransfer.log: ' + str(e))

    if 'tfrApply' in request.form:
        if not os.path.exists(iniFile):
            createConfigFile(iniFile)
        config = configparser.ConfigParser()
        try:
            config.read(iniFile)
            if not config.has_section('Transfer'):
                config.add_section('Transfer')
            config.set('Transfer', 'tfrMethod', str(request.form.get('tfrMethod')))
            if (request.form.get('tfrMethod') == 'FTP'):
                config.set('Transfer', 'ftpServer', str(request.form.get('ftpServer') or ''))
                config.set('Transfer', 'ftpUser', str(request.form.get('ftpUser') or ''))
                config.set('Transfer', 'ftpPassword', str(request.form.get('ftpPassword') or ''))
                ftpRemoteFolder = reformatSlashes(str(request.form.get('ftpRemoteFolder')))
                config.set('Transfer', 'ftpRemoteFolder', ftpRemoteFolder or '')
            elif (request.form.get('tfrMethod') == 'SFTP'):
                config.set('Transfer', 'sftpServer', str(request.form.get('sftpServer') or ''))
                config.set('Transfer', 'sftpUser', str(request.form.get('sftpUser') or ''))
                config.set('Transfer', 'sftpPassword', str(request.form.get('sftpPassword') or ''))
                sftpRemoteFolder = reformatSlashes(str(request.form.get('sftpRemoteFolder')))
                config.set('Transfer', 'sftpRemoteFolder', sftpRemoteFolder or '')
            elif (request.form.get('tfrMethod') == 'Dropbox'):
                config.set('Transfer', 'dbx_token', str(request.form.get('dbx_token') or ''))
            elif (request.form.get('tfrMethod') == 'Google Drive'):
                googleRemoteFolder = reformatSlashes(str(request.form.get('googleRemoteFolder')))
                config.set('Transfer', 'googleRemoteFolder', googleRemoteFolder or '')
            if (request.form.get('tfrMethod') != 'Off'):
                config.set('Transfer', 'transferDay', str(request.form.get('transferDay') or ''))
                config.set('Transfer', 'transferHour', str(request.form.get('transferHour') or ''))
            if not config.has_section('Copy'):
                config.add_section('Copy')
            config.set('Copy', 'copyDay', str(request.form.get('copyDay') or ''))
            config.set('Copy', 'copyHour', str(request.form.get('copyHour') or ''))
            with open(iniFile, 'w') as config_file:
                config.write(config_file)
        except Exception as e:
            app.logger.debug('INI file error writing: ' + str(e))
            if 'Permission denied' in str(e):
                flash('Permission denied writing to the ini file')
            else:
                flash('Error writing to the Ini file')

    return redirect(url_for('transfer'))


@app.route("/copyNow")
def copyNowCronJob():
    """
    This 'page' is only one of three called without the "@login_required" decorator. It's only called by
    the cron job/cameraTransfer.py script and will only execute if the calling IP is itself/localhost.
    """
    sourceIp = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if sourceIp != "127.0.0.1":
        abort(403)

    tasks = [
        copyNow.si(),
        newThumbs.si()
    ]
    chain(*tasks).apply_async()

    res = make_response('OK')
    return res, 200


@app.route("/thermal")
@login_required
def thermal():
    """ This page is where you monitor and manage the thermal settings & alarms."""

    templateData = {
        'thermalUnits'   : "Celsius",
        'arduinoTemp'    : 'Unknown',
        'arduinoMin'     : 'Unknown',
        'arduinoMax'     : 'Unknown',
        'piTemp'         : 'Unknown'
        }

    thermalUnits = request.cookies.get('thermalUnits')
    if thermalUnits == 'Fahrenheit' : templateData['thermalUnits'] = "Fahrenheit"

    try:
        writeString("GT") # Asks the Arduino to update its temperature string
        time.sleep(1);
        temperatures = str(readString("4")) # Reads the resulting string, a csv array
        templateData['arduinoTemp'] = temperatures.split(",")[0]
        templateData['arduinoMin']  = temperatures.split(",")[2]
        templateData['arduinoMax']  = temperatures.split(",")[1]
    except:
        pass
    templateData['piTemp'] = getPiTemp()

    return render_template('thermal.html', **templateData)


@app.route("/thermal", methods = ['POST'])    # The thermal page's POST method
@login_required
def thermalPOST():
    """ This page is where we act on the Reset buttons for max/min temp."""
    res = make_response("")

    if request.form.get('thermalUnits') == 'Celsius':
        res.set_cookie('thermalUnits', 'Celsius', 7 * 24 * 60 * 60)
    else:
        res.set_cookie('thermalUnits', 'Fahrenheit', 7 * 24 * 60 * 60)

    if 'resetMin' in request.form:
        app.logger.debug('thermal sent RN')
        writeString("RN") # Sends the Reset Min command to the Arduino
    if 'resetMax' in request.form:
        app.logger.debug('thermal sent RX')
        writeString("RX") # Sends the Reset Max command to the Arduino

    res.headers['location'] = url_for('thermal')
    return res, 302


@app.route("/system")
@login_required
def system():

    templateData = {
        'piThumbCount'   : '24',
        'arduinoDate'    : 'Unknown',
        'arduinoTime'    : 'Unknown',
        'piDateTime'     : 'Unknown',
        'piNtp'          : '',
        'piHostname'     : 'Unknown',
        'piUptime'       : 'Unknown',
        'piModel'        : 'Unknown',
        'piLinuxVer'     : 'Unknown',
        'piSpaceFree'    : 'Unknown',
        'wakePiTime'     : '',
        'wakePiDuration' : '',
        'rebootSafeWord' : REBOOT_SAFE_WORD,
        'intvlm8rVersion': 'Unknown',
        'cameraDateTime' : 'Unknown'
        }

    templateData['piThumbCount'] = getIni('Global', 'thumbsCount', 'int', '24')

    try:
        with open('/proc/device-tree/model', 'r') as myfile:
            templateData['piModel'] = myfile.read()
    except:
        pass

    try:
        with open("/etc/os-release") as f:
            release_info = dict()
            for line in f:
                key, value = line.rstrip().split("=")
                release_info[key] = value.strip('"')
                templateData['piLinuxVer'] = release_info["PRETTY_NAME"]
    except:
        pass

    try:
        templateData['arduinoDate'] = getArduinoDate() # Failure returns "Unknown"
        tempTime = getArduinoTime()                    # Failure returns "", on-screen as "Unknown"
        if tempTime != '':
                templateData['arduinoTime'] = tempTime
        rawWakePi = str(readString("5"))
        if rawWakePi != "Unknown":
            templateData['wakePiTime']     = rawWakePi[0:2]
            templateData['wakePiDuration'] = rawWakePi [2:4]
    except:
        pass

    templateData['piDateTime'] = datetime.now().strftime('%Y %b %d %H:%M:%S') #2019 Mar 08 13:06:03
    templateData['piNtp'] = checkNTP(None)

    try:
        templateData['piUptime']    = getPiUptime()
        templateData['piHostname']  = HOSTNAME
        templateData['piSpaceFree'],_ = getDiskSpace()
    except:
        pass

    try:
        with open('version', 'r') as versionFile:
            templateData['intvlm8rVersion'] = versionFile.read()
    except:
        pass

    try:
        camera, context, config = connectCamera()
        if camera:
            templateData['cameraDateTime'] = getCameraTimeAndDate(camera, context, config, 'Unknown')
            gp.check_result(gp.gp_camera_exit(camera))
    except:
        pass

    return render_template('system.html', **templateData)


@app.route("/system", methods = ['POST'])    # The camera's POST method
@login_required
def systemPOST():

    app.logger.debug('This is the /system POST page')

    if 'submitLocation' in request.form:
        try:
            newName = str(request.form.get('newName'))
            if newName != None:
                cache.set('locationName', newName, timeout = 0)
                app.logger.debug('New loc set as ' + newName)
                if not os.path.exists(iniFile):
                    createConfigFile(iniFile)
                config = configparser.ConfigParser()
                config.read(iniFile)
                if not config.has_section('Global'):
                    config.add_section('Global')
                config.set('Global', 'locationName', newName)
                with open(iniFile, 'w') as config_file:
                    config.write(config_file)
        except:
            app.logger.debug('Location set error')
            #pass

    if 'submitThumbsCount' in request.form:
        try:
            newCount = str(request.form.get('thumbsCount'))
            if newCount != None:
                app.logger.debug('New thumbs count set as ' + newCount)
                if not os.path.exists(iniFile):
                    createConfigFile(iniFile)
                config = configparser.ConfigParser()
                config.read(iniFile)
                if not config.has_section('Global'):
                    config.add_section('Global')
                config.set('Global', 'thumbsCount', newCount)
                with open(iniFile, 'w') as config_file:
                    config.write(config_file)
        except:
            app.logger.debug('New Thumbs set error')

    if 'wakePi' in request.form:
        app.logger.debug('Yes we got the WAKE PI button & values ' + str(request.form.get('wakePiTime')) + ', ' + str(request.form.get('wakePiDuration')) )
        WakePiHour = str(request.form.get('wakePiTime'))
        if WakePiHour == 'Always On':
            WakePiHour = '25'
        writeString("SP=" + WakePiHour + str(request.form.get('wakePiDuration')))

    if 'SyncSystem' in request.form:
        newTime = str(request.form.get('SyncSystem'))
        app.logger.debug('Yes we got the SyncSystem button & value ' + newTime)
        if request.form.get('setArduinoTime'):
            app.logger.debug('Checked: setArduinoTime')
            writeString("ST=" + newTime) # Send the new time and date to the Arduino
        if request.form.get('setPiTime'):
            app.logger.debug('Checked: setPiTime' )
            setTime(newTime)
        if request.form.get('setCameraTime'):
            app.logger.debug('Checked: setCameraTime')
            try:
                camera, context, config = connectCamera()
                if camera:
                    if setCameraTimeAndDate(camera, config, newTime):
                        # apply the changed config
                        camera.set_config(config)
                    else:
                        app.logger.debug('Failed to setCameraTimeAndDate')
                    camera.exit()
            except:
                pass

    if 'Reboot' in request.form:
        if str(request.form.get('rebootString')) == REBOOT_SAFE_WORD:
            writeString("RA")
            #app.logger.debug('Yes we got reboot safe word - ' + REBOOT_SAFE_WORD)
        else:
            pass
            #app.logger.debug('Button pressed but no reboot safe word - ' + REBOOT_SAFE_WORD)

    return redirect(url_for('system'))


def checkNTP(returnvalue):
    try:
        cmd = ['/bin/systemctl', 'is-active', 'systemd-timesyncd']
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, encoding='utf-8')
        (stdoutdata, stderrdata) = result.communicate()
        if stdoutdata:
            stdoutdata = stdoutdata.strip()
            if stdoutdata == 'active':
                app.logger.info('systemd-timesyncd = ' + str(stdoutdata) + '. The Pi takes its time from NTP')
                returnvalue = True
            else:
                app.logger.info('systemd-timesyncd = ' + str(stdoutdata) + '. The Pi does NOT take its time from NTP')
        if stderrdata:
            stderrdata = stderrdata.strip()
            app.logger.debug('systemd-timesyncd error = ' + str(stderrdata))
    except Exception as e:
        app.logger.debug('Unhandled systemd-timesyncd error: ' + str(e))
    return returnvalue


def setTime(newTime):
    """ Takes the time passed from the user's PC and sets the Pi's real time clock """
    try:
        #convert it to a form the date command will accept: Incoming is "20181129215800" representing "2018 Nov 29 21:58:00"
        timeCommand = ['/bin/date', '--set=%s' % datetime.strptime(newTime,'%Y%m%d%H%M%S')]
        result = subprocess.Popen(timeCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, encoding='utf-8')
        (stdoutdata, stderrdata) = result.communicate()
        if stdoutdata:
            stdoutdata = stdoutdata.strip()
            app.logger.debug('setTime result = ' + str(stdoutdata))
        if stderrdata:
            stderrdata = stderrdata.strip()
            app.logger.debug('setTime error = ' + str(stderrdata))
    except Exception as e:
        app.logger.debug('setTime unhandled time error: ' + str(e))


def connectCamera():
    app.logger.debug('connectCamera entered')
    retries = 0
    while True:
        app.logger.debug('connectCamera retries = {0}'.format (retries))
        if retries > 3:
            app.logger.debug('connectCamera returning None')
            return None, None, None
        try:
            camera = gp.Camera()
            context = gp.gp_context_new()
            camera.init(context)
            config = camera.get_config(context)
            app.logger.debug('connectCamera has made a connection to the camera. Exiting')
            break
        except gp.GPhoto2Error as e:
            app.logger.debug('connectCamera GPhoto2Error: ' + str(e))
            if e.string == 'Unknown model':
                if retries > 1:
                    app.logger.debug('connectCamera waking the camera & going again')
                    writeString("WC") # Sends the WAKE command to the Arduino
                    time.sleep(1);    # (Adds another second on top of the 0.5s baked into WriteString)
                else:
                    app.logger.debug('connectCamera going again without waking the camera')
                    time.sleep(0.5);
        except Exception as e:
            app.logger.debug('connectCamera error: ' + str(e))
        retries += 1
    app.logger.debug('connectCamera returning 3 values')
    return camera, context, config


def readValue ( camera, attribute ):
    """ Reads a simple attribute in the camera and returns the value """
    try:
        object = gp.check_result(gp.gp_widget_get_child_by_name(camera, attribute))
        value = gp.check_result(gp.gp_widget_get_value(object))
    except:
        value = 'Not available'
    return value


def readRange ( camera, context, group, attribute ):
    """
    Reads an attribute within a given group and returns the current setting and all the possible options
    It's only called by "camera" and "main" when we already have an established connection to the
    camera, so it's inappropriate (and inefficient) to attempt a reconnection here.
    """
    options = []
    currentValue = 'Unknown'
    try:
        config_tree = camera.get_config(context)
        total_child = config_tree.count_children()
        for i in range(total_child):
            child = config_tree.get_child(i)
            if (child.get_name() == group):
                for a in range(child.count_children()):
                    grandchild = child.get_child(a)
                    try:
                        if (grandchild.get_name() == attribute):
                            currentValue = grandchild.get_value()
                            for k in range(grandchild.count_choices()):
                                choice = grandchild.get_choice(k)
                                options.append(choice)
                    except:
                        pass
                        #break   #We have found and extracted the attribute we were seeking
    except Exception as e:
        app.logger.debug('readRange threw: ' + str(e))
    return currentValue, options


def getCameraTimeAndDate( camera, context, config, returnvalue ):
    try:
        # find the date/time setting config item and get it
        # name varies with camera driver
        #   Canon EOS350d - 'datetime'
        #   PTP - 'd034'
        for name, fmt in (('datetime', '%Y %b %d %H:%M:%S'),
                          ('datetimeutc', None),
                          ('d034',     None)):
            OK, datetime_config = gp.gp_widget_get_child_by_name(config, name)
            if OK >= gp.GP_OK:
                widget_type = gp.check_result(gp.gp_widget_get_type(datetime_config))
                if widget_type == gp.GP_WIDGET_DATE:
                    raw_value = gp.check_result(
                        gp.gp_widget_get_value(datetime_config))
                    returnvalue = datetime.fromtimestamp(raw_value).strftime('%Y %b %d %H:%M:%S')
                else:
                    raw_value = gp.check_result(gp.gp_widget_get_value(datetime_config))
                    if fmt:
                        camera_time = datetime.strptime(raw_value, fmt)
                    else:
                        camera_time = datetime.utcfromtimestamp(float(raw_value))
                    returnvalue = camera_time.isoformat(' ')
                break
    except Exception as e:
        app.logger.debug('Error reading camera time and date: ' + str(e))
    return returnvalue


def setCameraTimeAndDate(camera, config, newTimeDate):
    """
    Straight out of Jim's examples again, this time from "set-camera-clock.py" (with some tweaks)
    """
    abilities = camera.get_abilities()
    # get configuration tree
    OK, date_config = gp.gp_widget_get_child_by_name(config, 'datetimeutc')
    if OK >= gp.GP_OK:
        app.logger.debug('Set camera time (opt 1)')
        now = time.strptime(newTimeDate,'%Y%m%d%H%M%S')
        epochTime = int(time.mktime(now))
        date_config.set_value(epochTime)
        return True
    OK, date_config = gp.gp_widget_get_child_by_name(config, 'datetime')
    if OK >= gp.GP_OK:
        widget_type = date_config.get_type()
        if widget_type == gp.GP_WIDGET_DATE:
            app.logger.debug('Set camera time (opt 2)')
            now = time.strptime(newTimeDate,'%Y%m%d%H%M%S')
            epochTime = int(time.mktime(now))
            app.logger.debug('epochTime = {0}'.format(epochTime))
            date_config.set_value(epochTime)
        else:
            app.logger.debug('Set camera time (opt 3)')
            now = time.strptime(newTimeDate,'%Y%m%d%H%M%S')
            newNow = time.strftime('%Y-%m-%d %H:%M:%S', now)
            date_config.set_value(newNow)
        return True
    app.logger.debug('Failed to set camera time')
    return False


def list_camera_files(camera, path='/'):
    """ Returns a list of all the image files on the camera """
    result = []
    # get files
    for name, value in gp.check_result(
            gp.gp_camera_folder_list_files(camera, path)):
        result.append(os.path.join(path, name))
    # read folders
    folders = []
    for name, value in gp.check_result(
            gp.gp_camera_folder_list_folders(camera, path)):
        folders.append(name)
    # recurse over subfolders
    for name in folders:
        result.extend(list_camera_files(camera, os.path.join(path, name)))
    return result


def list_Pi_Images(path):
    result = []
    for root, dirs, files in os.walk(os.path.expanduser(path)):
        for name in files:
            if '.thumbs' in dirs:
                dirs.remove('.thumbs')
            if name in ('.directory',):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in ('.db',):
                continue
            if ext in ('.txt',):
                continue
            result.append(os.path.join(root, name))
    return result


def get_camera_file_info(camera, path):
    """ Returns the details of the specific image passed in """
    folder, name = os.path.split(path)
    return gp.check_result(
        gp.gp_camera_file_get_info(camera, folder, name))


def files_to_copy(camera):
    newFilesList = []
    if not os.path.isdir(PI_PHOTO_DIR):
        os.makedirs(PI_PHOTO_DIR)
    computer_files = list_Pi_Images(PI_PHOTO_DIR)
    camera_files = list_camera_files(camera)
    if not camera_files:
        app.logger.debug('No files found')
        return
    for path in camera_files:
        sourceFolderTree, imageFileName = os.path.split(path)
        dest = CreateDestPath(sourceFolderTree, PI_PHOTO_DIR)
        dest = os.path.join(dest, imageFileName)
        if dest in computer_files:
            continue
        newFilesList.append(path)
    return newFilesList


def copy_files(camera, imageToCopy, deleteAfterCopy):
    """ Straight from Jim's examples again """
    app.logger.debug('Copying files...')
    sourceFolderTree, imageFileName = os.path.split(imageToCopy)
    dest = CreateDestPath(sourceFolderTree, PI_PHOTO_DIR)
    dest = os.path.join(dest, imageFileName)
    app.logger.debug('Copying {0} --> {1}'.format(imageToCopy, dest))
    try:
        camera_file = gp.check_result(gp.gp_camera_file_get(
            camera, sourceFolderTree, imageFileName, gp.GP_FILE_TYPE_NORMAL))
        copyOK = gp.check_result(gp.gp_file_save(camera_file, dest))
        if (copyOK >= gp.GP_OK):
            if (deleteAfterCopy == True):
                gp.check_result(gp.gp_camera_file_delete(camera, sourceFolderTree, imageFileName))
                app.logger.info('Deleted {0}/{1}'.format(sourceFolderTree, imageFileName))
    except Exception as e:
        app.logger.info('Exception in copy_files: ' + str(e))
    return 0


def CreateDestPath(folder, NewDestDir):
    try:
        ImageSubDir = re.search(("DCIM/\S*"), folder)
        if ImageSubDir != None:
            subdir = os.path.join(NewDestDir, ImageSubDir.group(0))
            # app.logger.debug('Subdir =  ' + subdir)
            try:
                if not os.path.isdir(subdir):
                    os.makedirs(subdir)
            except:
                app.logger.debug("Didn't want to make " + subdir)
            dest = os.path.join(NewDestDir, subdir)
            # app.logger.debug('Pi dest = ' + dest)
        else:
            dest = NewDestDir
    except Exception as e:
        app.logger.debug('Error in DCIM decoder: ' + str(e))
        dest = NewDestDir
    return dest


def createDestFilename(imageFullFilename, targetFolder, suffix):
    """
    Called by 'makeThumb', /main and /thumbnails
    Manipulates the path and filename of every image:
    - Changes its source path to the targetFolder directory
    - And adds the nominated suffix
    """
    sourceFolderTree, imageFileName = os.path.split(imageFullFilename)
    dest = CreateDestPath(sourceFolderTree, targetFolder)
    dest = os.path.join(dest, imageFileName)
    dest = re.sub('.JPG|.CR2|.NEF', (suffix + '.JPG'), dest, flags=re.IGNORECASE)
    return dest


def makeThumb(imageFile):
    try:
        _, imageFileName = os.path.split(imageFile)
        dest = createDestFilename(imageFile, PI_THUMBS_DIR, '-thumb')
        app.logger.debug('Thumb dest = ' + dest)
        alreadyExists = False
        if os.path.exists(dest):
            app.logger.debug('Thumbnail already exists.') #This logs to /var/log/celery/celery_worker.log
            alreadyExists = True
        else:
            app.logger.info('We need to make a thumbnail of {0}'.format(imageFile)) #This logs to /var/log/celery/celery_worker.log
            try:
                while True:
                    if imageFile.endswith(RAWEXTENSIONS):
                        #It's a RAW:
                        with rawpy.imread(imageFile) as raw:
                            # (1/2) See if we can extract a large-format JPG to use internally
                            try:
                                rgb = raw.postprocess()
                                previewfilename = createDestFilename(imageFile, PI_PREVIEW_DIR, '-preview')
                                imageio.imwrite(previewfilename, rgb)
                                app.logger.info('makeThumb() rawpy extracted preview   from RAW OK')
                            except Exception as e:
                                app.logger.info('makeThumb() unknown rawpy preview error: ' + str(e))
                            # (2/2) See if we can extract a pre-made thumb
                            try:
                                thumb = raw.extract_thumb()
                                if thumb.format == rawpy.ThumbFormat.JPEG:
                                    # thumb.data is already in JPEG format, save as-is
                                    with open(dest, 'wb') as f:
                                        f.write(thumb.data)
                                        app.logger.info('makeThumb() rawpy extracted thumbnail from RAW OK')
                                        break
                                elif thumb.format == rawpy.ThumbFormat.BITMAP:
                                    # thumb.data is an RGB numpy array, convert with imageio
                                    imageio.imwrite(dest, thumb.data)
                                    app.logger.info('makeThumb() rawpy extracted bitmap thumbnail from RAW OK')
                                    break
                                else:
                                    #No can do? Let PIL handle it.
                                    pass
                            except rawpy.LibRawNoThumbnailError as e:
                                app.logger.info('makeThumb() rawpy LibRawNoThumbnailError error: ' + str(e))
                            except rawpy.LibRawUnsupportedThumbnailError as e:
                                app.logger.info('makeThumb() rawpy LibRawUnsupportedThumbnailError error: ' + str(e))
                            except Exception as e:
                                app.logger.info('makeThumb() unknown rawpy save error: ' + str(e))
                    else:
                        app.logger.info('makeThumb() image filename {0} is not RAW'.format(imageFile))
                    with Image.open(imageFile) as thumb:
                        thumb.thumbnail((160, 160), Image.ANTIALIAS)
                        thumb.save(dest, "JPEG")
                        break
            except Exception as e:
                app.logger.info('makeThumb() thumbnail save error: ' + str(e))
        getExifData(imageFile, imageFileName)
        return dest, alreadyExists
    except Exception as e:
        app.logger.info('Unknown Exception in makeThumb(): ' + str(e))
        return None, None


def getExifData(imageFilePath, imageFileName):
    while True:
        #Lots of TRYs here to minimise any bad data errors in the output.
        try:
            # Open image file for reading (binary mode)
            abort = None
            with open(imageFilePath, 'rb') as photo:
                tags = exifreader.process_file(photo) # Return Exif tags.
            try:
                dateOriginal = ''
                timeOriginal = ''
                dateTimeOriginal = str(tags['EXIF DateTimeOriginal']).split(' ')
                dateOriginal = (dateTimeOriginal[0]).replace(':', '/')
                timeOriginal = dateTimeOriginal[1]
            except Exception as e:
                app.logger.info('getExifData() dateTimeOriginal error: ' + str(e))
            if os.path.exists(PI_THUMBS_INFO_FILE):
                with open(PI_THUMBS_INFO_FILE, 'rt') as f:
                    for line in f:
                        if ('{0} = {1} {2}|'.format(imageFileName, dateOriginal, timeOriginal)) in line:
                            app.logger.info('getExifData() image {0} already exists in Exif file. Aborting'.format(imageFileName))
                            abort = True
                            break
            if abort:
                break
            try:
                _, fileExtension = os.path.splitext(imageFilePath)
                fileExtension = fileExtension.upper().replace('.', '') #Convert to upper case and delete the dot
            except Exception as e:
                fileExtension = '?'
                app.logger.info('getExifData() fileExtension error: ' + str(e))
            try:
                #Reformat depending on the value:
                # 6/1   becomes 6s
                # 15/10 becomes 1.5s
                # 3/10  becomes 0.3s
                # 1/30  becomes 1/30s
                exposureTime = convert_to_float(str(tags['EXIF ExposureTime']))
                if (exposureTime).is_integer():
                    #It's a whole number of seconds. Strip the '.0'
                    exposureTime = str(exposureTime).replace('.0','')
                elif (Decimal(exposureTime).as_tuple().exponent <= -2):
                    #Yuk. it has lots of decimal places. Display as originally reported
                    exposureTime = str(tags['EXIF ExposureTime'])
                else:
                    pass #We'll stick with the originally calculated exposure time, which will be 1 decimal place below 1s, e.g. 0.3
            except Exception as e:
                exposureTime = '?'
                app.logger.info('getExifData() ExposureTime error: ' + str(e))
            try:
                fNumber = str(convert_to_float(str(tags['EXIF FNumber'])))
                #Strip the '.0' if it's a whole F-stop
                fNumber = fNumber.replace('.0','')
            except Exception as e:
                fNumber = '?'
                app.logger.info('getExifData() fNumber error: ' + str(e))
            try:
                ISO = tags['EXIF ISOSpeedRatings']
            except Exception as e:
                ISO = '?'
                app.logger.info('getExifData() ISO error: ' + str(e))
            try:
                with open(PI_THUMBS_INFO_FILE, "a") as thumbsInfoFile:
                    thumbsInfoFile.write('{0} = {1} {2}|{3} &bull; {4}s &bull; F{5} &bull; ISO{6}\r\n'.format(imageFileName, dateOriginal, timeOriginal, fileExtension, exposureTime, fNumber, ISO))
            except Exception as e:
                app.logger.info('getExifData() error writing to thumbsInfoFile: ' + str(e))
            break
        except Exception as e:
            app.logger.info('getExifData() EXIF error: ' + str(e))
            break
    return


def dedupeExifData():
    lines = 0
    ThumbsInfo = {}
    if os.path.exists(PI_THUMBS_INFO_FILE):
        with open(PI_THUMBS_INFO_FILE, 'rt') as f:
            for line in f:
                if ' = ' in line:
                    try:
                        lines += 1
                        (key, val) = line.rstrip('\n').split(' = ')
                        ThumbsInfo[key] = val
                    except Exception as e:
                        #Skip over bad line
                        app.logger.debug('dedupeExifData info file error: ' + str(e))
        if lines != len(ThumbsInfo):
            #We have a discrepancy (dupe or bad line). Re-write the file:
            app.logger.info('dedupeExifData() recreating thumbs info file: lines = {0}, UniqueImages = {1}'.format(lines, len(ThumbsInfo)))
            with open(PI_THUMBS_INFO_FILE, 'r+') as file:
                file.seek(0)
                for key, value in ThumbsInfo.items():
                    file.write('{0} = {1}\n'.format(key, value))
                file.truncate() #Trash the leftovers.
    return


#TY SO: https://stackoverflow.com/a/30629776
def convert_to_float(frac_str):
    """ The EXIF exposure time and f-number data is a string representation of a fraction. This converts it to a float for display """
    try:
        return float(frac_str)
    except ValueError:
        num, denom = frac_str.split('/')
        try:
            leading, num = num.split(' ')
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac


def getPreviewImage(camera, context, config):
    """ Straight out of Jim's examples """
    OK, image_format = gp.gp_widget_get_child_by_name(config, 'imageformat')
    if OK >= gp.GP_OK:
        # get current setting
        value = gp.check_result(gp.gp_widget_get_value(image_format))
        # make sure it's not raw
        if 'raw' in value.lower():
            app.logger.debug('Cannot preview raw images')
            return 1
    # find the capture size class config item
    # need to set this on my Canon 350d to get preview to work at all
    OK, capture_size_class = gp.gp_widget_get_child_by_name(
        config, 'capturesizeclass')
    if OK >= gp.GP_OK:
        # set value
        value = gp.check_result(gp.gp_widget_get_choice(capture_size_class, 2))
        gp.check_result(gp.gp_widget_set_value(capture_size_class, value))
        # set config
        gp.check_result(gp.gp_camera_set_config(camera, config))
    # capture preview image (not saved to camera memory card)
    app.logger.debug('Capturing preview image')
    camera_file = gp.check_result(gp.gp_camera_capture_preview(camera))
    file_data = gp.check_result(gp.gp_file_get_data_and_size(camera_file))
    # display image
    data = memoryview(file_data)
    app.logger.debug(type(data), len(data))
    app.logger.debug(data[:10].tolist())
    fileName = os.path.join(PI_PREVIEW_DIR, PI_PREVIEW_FILE)
    if os.path.exists(fileName):
        os.remove(fileName)
    Image.open(io.BytesIO(file_data)).save(fileName, "JPEG")
    return 0


def getDiskSpace():
    """ https://www.raspberrypi.org/forums/viewtopic.php?t=22180 """
    try:
        disk = psutil.disk_usage('/')
        #disk_total = disk.total / 2**30     # GiB.
        #disk_used = disk.used / 2**30
        disk_free_bytes = disk.free
        disk_free_str = str(round(disk_free_bytes / 2**30,2)) + ' GB'
    except:
        return "Unknown",None
    return disk_free_str,disk_free_bytes


def createConfigFile(iniFile):
    """ Thank you https://www.blog.pythonlibrary.org/2013/10/25/python-101-an-intro-to-configparser/ """
    try:
        config = configparser.ConfigParser()
        config.add_section('Global')
        config.set('Global', 'file created', time.strftime("%0d %b %Y",time.localtime(time.time())))
        config.set('Global', 'thumbscount', '24')
        config.add_section('Transfer')
        config.set('Transfer', 'tfrMethod', 'Off')
        config.set('Transfer', 'deleteAfterTransfer', 'Off')
        config.add_section('Copy')
        config.set('Copy', 'copyDay', 'Daily')
        config.set('Copy', 'copyHour', '14')
        config.set('Copy', 'deleteAfterCopy', 'Off')
        with open(iniFile, 'w') as config_file:
            config.write(config_file)
    except:
        app.logger.debug('createConfigFile Threw creating ' + iniFile)
    return


def getIni(keySection, keyName, keyType, defaultValue):
    """
    Reads a key from the INI file and returns its value.
    If it doesn't exist, it's created with a default value, which is then returned.
    """
    returnValue = defaultValue
    try:
        if not os.path.exists(iniFile):
            createConfigFile(iniFile)
        config = configparser.ConfigParser()
        config.read(iniFile)
        if 'bool' in keyType:
            returnValue = config.getboolean(keySection, keyName)
        else:
            returnValue = config.get(keySection, keyName)
    except configparser.Error as e:
        app.logger.info('getIni() reports key error: ' + str(e))
        #Looks like the flag doesn't exist. Let's add it
        try:
            if not config.has_section(keySection):
                config.add_section(keySection)
            config.set(keySection, keyName, defaultValue)
            with open(iniFile, 'w') as config_file:
                config.write(config_file)
            app.logger.debug('Added {0} key {1}/{2} with a value of {3}'.format(keyType, keySection, keyName, defaultValue))
        except Exception as e:
            app.logger.debug('Exception thrown trying to add {0} key {1}/{2} with a value of {3}'.format(keyType, keySection, keyName, defaultValue))
    except Exception as e:
        app.logger.info('Unhandled error in getIni(): ' + str(e))
    return returnValue


@app.route('/trnCopyNow', methods=['POST'])
@login_required
def trnCopyNow():
    """
    This page is called in the background by the 'Copy now' button on the Transfer page
    It kicks off the background task, and returns the taskID so its progress can be followed
    """
    app.logger.debug('trnCopyNow() entered')
    app.logger.debug('[See /var/log/celery/celery_worker.log for what happens here]')

    tasks = [
        copyNow.si(),
        newThumbs.si()
    ]
    task = chain(*tasks).apply_async()

    app.logger.debug('trnCopyNow() returned with task_id= ' + str(task.id))
    return jsonify({}), 202, {'Location': url_for('backgroundStatus', task_id=task.id)}


@celery.task(time_limit=1800, bind=True)
def copyNow(self):
    writeString("WC") # Sends the camera WAKE command to the Arduino
    app.logger.info('copyNow() entered') #This logs to /var/log/celery/celery_worker.log
    camera = gp.Camera()
    context = gp.gp_context_new()
    retries = 0
    filesToCopy = []
    while True:
        time.sleep(1);  # Pause between retries
        retries += 1
        if retries >= 6:
            #We've waited too long. Abort.
            app.logger.info('copyNow() could not claim the USB device after ' + str(retries) + ' attempts.')
            return {'status': 'USB error'}
        try:
            app.logger.info('copyNow() trying to init the camera')
            camera.init(context)
            #The line above will throw an exception if we can't connect to the camera
            break
        except gp.GPhoto2Error as e:
            app.logger.info("copyNow() wasn't able to connect to the camera: " + e.string)
            continue
        except Exception as e:
            app.logger.info('Unknown error in copyNow(): ' + str(e))
            continue
    self.update_state(state='PROGRESS', meta={'status': 'Preparing to copy images'})
    thisImage = 0
    filesToCopy = files_to_copy(camera)
    if filesToCopy:
        numberToCopy = len(filesToCopy)
        app.logger.info('copyNow(self) has been tasked with copying ' + str(numberToCopy) + ' images')
        deleteAfterCopy = getIni('Copy', 'deleteAfterCopy', 'bool', 'Off')
        while len(filesToCopy) > 0:
            try:
                thisImage += 1
                self.update_state(state='PROGRESS', meta={'status': 'Copying image ' + str(thisImage) + ' of ' + str(numberToCopy)})
                thisFile = filesToCopy.pop(0)
                app.logger.info('About to copy file: ' + str(thisFile))
                copy_files(camera, thisFile, deleteAfterCopy)
            except Exception as e:
                app.logger.info('Unknown error in copyNow(self): ' + str(e))
    try:
        gp.check_result(gp.gp_camera_exit(camera))
        app.logger.info('copyNow() ended happily')
    except Exception as e:
        app.logger.info('copyNow() ended sad: ' + str(e))
    if thisImage == 0:
        statusMessage = "There were no new images to copy"
    else:
        statusMessage = 'Copied ' + str(thisImage) + ' images OK'
    return {'status': statusMessage}


@celery.task(time_limit=1800, bind=True)
def newThumbs(self):
    app.logger.info('newThumbs() entered') #This logs to /var/log/celery/celery_worker.log
    try:
        FileList  = list_Pi_Images(PI_PHOTO_DIR)
        ThumbList = list_Pi_Images(PI_THUMBS_DIR)
        PI_PHOTO_COUNT = len(FileList)
        PI_THUMB_COUNT = len(ThumbList)
        if PI_PHOTO_COUNT - PI_THUMB_COUNT <= 0:
            thumbsToCreate = 'Unknown'
            app.logger.info('Thumbs to create = ' + thumbsToCreate)
        else:
            thumbsToCreate = str(PI_PHOTO_COUNT - PI_THUMB_COUNT)
        thumbsCreated = 0
        app.logger.info('Thumbs to create = ' + thumbsToCreate)
        if PI_PHOTO_COUNT >= 1:
            #Read the thumb files themselves:
            for loop in range(-1, (-1 * (PI_PHOTO_COUNT + 1)), -1):
                dest, alreadyExists = makeThumb(FileList[loop]) #Create a thumb, and metadata for every image on the Pi
                if (dest == None):
                    #Something went wrong
                    app.logger.debug('A thumb was not created for {0}'.format(FileList[loop]))
                    continue
                if not alreadyExists:
                    thumbsCreated += 1
                    self.update_state(state='PROGRESS', meta={'status': 'Created thumbnail ' + str(thumbsCreated) + ' of ' + thumbsToCreate})
                    app.logger.info('Thumb  of {0} is {1}'.format(FileList[loop], dest))
                else:
                    app.logger.debug('Thumb for ' + dest + ' already exists')
        else:
            app.logger.info('There are no images on the Pi. Copy some from the Transfer page.')
    except Exception as e:
        app.logger.info('newThumbs error: ' + str(e))
    dedupeExifData()
    app.logger.info('newThumbs() returned')
    return {'status': 'Created ' + str(thumbsCreated) + ' thumbnail images OK'}


# TY Miguel: https://blog.miguelgrinberg.com/post/using-celery-with-flask
@app.route('/backgroundStatus/<task_id>')
@login_required
def backgroundStatus(task_id):
    task = copyNow.AsyncResult(task_id)
    app.logger.debug('backgroundStatus() entered with task_id = ' + task_id + ' and task.state = ' + str(task.state))
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state,
            'status': 'Background task pending'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
    else:
        # something went wrong in the background job
        app.logger.debug("Something went wrong in the background job: {0}".format(task.info))
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    app.logger.debug('backgroundStatus() returned')
    return jsonify(response)


# https://stackoverflow.com/questions/5544629/retrieve-list-of-tasks-in-a-queue-in-celery
@app.before_request
def getCeleryTasks():
    """
    This executes before EVERY page load, feeding any active task ID into the
    ensuing response. Javascript in the footer of every page (in index.html)
    will then query for status updates if a task ID is present.
    """
    try:
        # Inspect all nodes.
        i = celery.control.inspect(['celery_worker@' + HOSTNAME])
        # Show tasks that are currently active.
        activeTasks = i.active()
        if activeTasks != None:
            for _, tasks in list(activeTasks.items()):
                if tasks:
                    g.taskstr = ','.join("%s" % (t['id']) for t in tasks[:1]) #Just the first task will do
                else:
                    #app.logger.debug('getCeleryTasks cleared g.taskstr')
                    g.taskstr = None
            #app.logger.debug("getCeleryTasks g.taskstr = {0}".format(g.taskstr))
        else:
            app.logger.debug('getCeleryTasks reports there are no activeTasks')
    except Exception as e:
        app.logger.debug('getCeleryTasks exception: ' + str(e))


def reformatSlashes(folder):
    """
    Reformat the user's remote folder value:
    1) Convert any backslashes to slashes
    2) Convert any double slashes to singles
    """
    while '\\' in folder:
        folder = folder.replace('\\', '/') # Escaping means the '\\' here is seen as a single backslash
    while '//' in folder:
        folder = folder.replace('//', '/')
    return folder


def getLargestImageSize(path):
    '''
    Finds the largest file on the /photos/ folder tree.
    Used to calculate the number of days' worth of storage left on the Pi
    '''    
    max_size = 0
    try:
        for folder, subfolders, files in os.walk(path):
            # checking the size of each file
            for file in files:
                size = os.stat(os.path.join( folder, file  )).st_size
                # updating maximum size
                if size > max_size:
                    max_size = size
        app.logger.debug('getLargestImageSize returned: ' + str(max_size))
        return max_size
    except Exception as e:
        app.logger.debug('getLargestImageSize exception: ' + str(e))
        return None

    
def getShotsPerDay():
    '''
    Used to calculate the number of days' worth of storage left on the Pi and camera
    '''
    shotsPerDay = 0
    try:
        ArdInterval = str(readString("3"))
        #Returns a string that's <DAY> (a byte to be treated as a bit array of days) followed by 2-digit strings of <startHour>, <endHour> & <Interval>:
        if (ArdInterval != "Unknown") & (len(ArdInterval) == 7):
            startHour = int(ArdInterval[1:3])
            endHour   = int(ArdInterval[3:5])
            interval  = int(ArdInterval[5:7])
            if endHour >= startHour:
                shotsPerDay = (endHour - startHour) * (60 / interval)
            else:
                shotsPerDay = ((endHour + 24) - startHour) * (60 / interval) #Future: when I finally code overnight shot handling
            app.logger.debug('getShotsPerDay returned: ' + str(shotsPerDay))
            return shotsPerDay
        else:
            return None
    except Exception as e:
        app.logger.debug('getShotsPerDay exception: ' + str(e))
        return None


#This always needs to be at the end, as nothing else will run after it - it's blocking:
if __name__ == "__main__":
   app.run(host='0.0.0.0')
