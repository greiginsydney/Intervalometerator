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
from PIL import Image   #For the camera page / preview button
from urllib.parse import urlparse, urljoin
import calendar
import configparser # for the ini file (used by the Transfer page)
import fnmatch # Used for testing filenames
import logging
import importlib.util # Testing installed packages
import io   #Camera preview
import os
import psutil
import re    #RegEx. Used in Copy Files
from smbus2 import SMBus # For I2C
import struct
import subprocess
import sys
import time

import gphoto2 as gp

from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

from werkzeug.security import check_password_hash

from flask import Flask, flash, render_template, request, redirect, url_for, make_response, abort
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin, login_url
app = Flask(__name__)
app.secret_key = b'### Paste the secret key here. See the Setup docs ###' #Cookie for session messages
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = ''


# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

PI_PHOTO_DIR  = os.path.expanduser('/home/pi/photos')
PI_THUMBS_DIR = os.path.expanduser('/home/pi/thumbs')
PI_PREVIEW_DIR = os.path.expanduser('/home/pi/preview')
PI_PREVIEW_FILE = 'intvlm8r-preview.jpg'
PI_TRANSFER_DIR = os.path.expanduser('/home/pi/www/static')
PI_TRANSFER_FILE = os.path.join(PI_TRANSFER_DIR, 'piTransfer.log')
PI_TRANSFER_LINK = 'static/piTransfer.log' #This is the file that the Transfer page will link to when you click "View Log"
gunicorn_logger = logging.getLogger('gunicorn.error')
REBOOT_SAFE_WORD = 'sayonara'

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

arduinoDoW=["Unknown", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

hiddenTransferOptions = ''
# TY SO: https://stackoverflow.com/a/41815890
for package_name in ('paramiko', 'dropbox', 'Google Drive'):
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        app.logger.debug(package_name + ' is not installed')
        hiddenTransferOptions = hiddenTransferOptions + "," + package_name
        

def writeString(value):
    ascii = [ord(c) for c in value]
    for x in range(0, 2):
        try:
            bus.write_i2c_block_data(address, 0, ascii)
        except Exception as e:
            app.logger.debug('writeString error:' + str(e))
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
            app.logger.debug('readString error:' + str(e))
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
        app.logger.debug('Pi temp error:' + str(e))
    app.logger.debug('Pi temp = ' + temp)
    return temp


@app.context_processor
def customisation():
    loc = cache.get('locationName')
    if loc is None:
        #The cache is empty? Read the location from the Ini file
        config = configparser.ConfigParser({'locationName' : 'Intervalometerator'})
        config.read(iniFile)
        try:
            loc = config.get('Global', 'locationName') #This will fail the VERY first time the script runs
        except:
            loc = 'Intervalometerator'
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
        app.logger.debug('Its a GET to LOGIN')
        return render_template('login.html')
    username = (str(request.form['username'])).lower() #Don't care for case in a username
    if username in users:
        #if (check_password_hash(users[username]['password'], request.form['password'])):
        if users[username]['password'] == request.form['password']:
            user = User()
            user.id = username
            remember = 'false'
            if request.form.get('rememberme'):
                remember = 'true'
            login_user(user,'remember=' + remember)
            app.logger.debug('Logged-in ' + username)
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
    flash('You need to sign in before you can access that page!')
    return redirect(login_url(url_for('login'), request.url))


@app.route("/")
@login_required
def main():
    templateData = {
        'arduinoDate'       : 'Unknown',
        'arduinoTime'       : '',
        'arduinoLastShot'   : 'Unknown',
        'arduinoNextShot'   : 'Unknown',
        'cameraModel'       : '',
        'cameraLens'        : 'Unknown',
        'cameraBattery'     : 'Unknown',
        'fileCount'         : 'Unknown',
        'lastImage'         : 'Unknown',
        'availableShots'    : 'Unknown',
        'piInterval'        : '',
        'piImageCount'      : 'Unknown',
        'piLastImage'       : 'Unknown',
        'piSpaceFree'       : 'Unknown',
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
        camera = gp.Camera()
        context = gp.gp_context_new()
        camera.init(context)

        storage_info = gp.check_result(gp.gp_camera_get_storageinfo(camera))
        if len(storage_info) == 0:
            flash('No storage info available') # The memory card is missing or faulty
            
        abilities = gp.check_result(gp.gp_camera_get_abilities(camera))
        config = camera.get_config(context)
        files = list_camera_files(camera)
        if not files:
            fileCount = 0
            lastImage = ''
        else:
            fileCount = len(files)
            info = get_camera_file_info(camera, files[-1]) #Get the last file
            lastImage = datetime.utcfromtimestamp(info.file.mtime).isoformat(' ')
        gp.check_result(gp.gp_camera_exit(camera))
        templateData['cameraModel']              = abilities.model
        templateData['cameraLens'], discardMe    = readRange (camera, context, 'status', 'lensname')
        templateData['fileCount']                = fileCount
        templateData['lastImage']                = lastImage
        templateData['availableShots']           = readValue (config, 'availableshots')
        templateData['cameraBattery'], discardMe = readRange (camera, context, 'status', 'batterylevel')
    except gp.GPhoto2Error as e:
        flash(e.string)
        app.logger.debug('GPhoto camera error in main:' + str(e))
    except Exception as e:
        app.logger.debug('Unknown camera error in main:' + str(e))

    # Pi comms:
    piLastImage = ''
    piLastImageFile = ''
    try:
        FileList = list_Pi_Images(PI_PHOTO_DIR)
        PI_PHOTO_COUNT = len(FileList)
        if PI_PHOTO_COUNT >= 1:
            FileList.sort(key=lambda x: os.path.getmtime(x))
            piLastImage = datetime.utcfromtimestamp(os.path.getmtime(FileList[-1])).replace(microsecond=0)
            piLastImageFile = str(FileList[-1]).replace((PI_PHOTO_DIR  + "/"), "")
    except:
        flash('Error talking to the Pi')
        PI_PHOTO_COUNT = 0
    templateData['piImageCount']    = PI_PHOTO_COUNT
    templateData['piLastImage']     = piLastImage
    templateData['piSpaceFree']     = getDiskSpace()
    templateData['piLastImageFile'] = piLastImageFile
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
    This 'page' is only one of two called without the "@login_required" decorator. It's only called by 
    the cron job/script and will only execute if the calling IP is itself/localhost.
    """
    sourceIp = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if sourceIp != "127.0.0.1":
        abort(403)
    arduinoDate = getArduinoDate()
    arduinoTime = getArduinoTime()
    res = make_response('<div id="dateTime">' + arduinoDate + ' ' + arduinoTime + '</div>')
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
    ThumbFiles = []

    if not os.path.exists(iniFile):
        createConfigFile(iniFile)
    config = configparser.ConfigParser()
    config.read(iniFile)
    try:
        ThumbsToShow = int(config.get('Global', 'thumbsCount'))
    except Exception as e:
        app.logger.debug('INI file error reading:' + str(e))
        ThumbsToShow = 20

    try:
        FileList  = list_Pi_Images(PI_PHOTO_DIR)
        ThumbList = list_Pi_Images(PI_THUMBS_DIR)
        PI_PHOTO_COUNT = len(FileList)
        if PI_PHOTO_COUNT >= 1:
            FileList.sort(key=lambda x: os.path.getmtime(x))

            ThumbnailCount = min(ThumbsToShow,PI_PHOTO_COUNT) # The lesser of these two values
            for loop in range(-1, (-1 * (ThumbnailCount + 1)), -1):
                sourceFolderTree, imageFileName = os.path.split(FileList[loop])
                dest = CreateDestPath(sourceFolderTree, PI_THUMBS_DIR)
                dest = os.path.join(dest, imageFileName)
                dest = dest.replace('.JPG', '-thumb.JPG')
                app.logger.debug('Thumb dest = ' + dest)
                # This adds the shortened path to the list to pass to the web-page
                ThumbFiles.append(str(dest).replace((PI_THUMBS_DIR  + "/"), ""))
                if dest in ThumbList:
                    app.logger.debug('Thumbnail exists')
                    continue
                try:
                    thumb = Image.open(str(FileList[loop]))
                    thumb.thumbnail((128, 128), Image.ANTIALIAS)
                    thumb.save(dest, "JPEG")
                except Exception as e:
                    app.logger.debug('Thumbs Pillow error: ' + str(e))
        else:
            flash("There are no images on the Pi. Copy some from the Transfer page.")
            
    except Exception as e:
        app.logger.debug('Thumbs error: ' + str(e))
    return render_template('thumbnails.html', ThumbFiles = ThumbFiles)


@app.route("/camera")
@login_required
def camera():
    cameraData = {
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
        'piPreviewFile' : ''
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
        camera = gp.Camera()
        context = gp.gp_context_new()
        camera.init(context)
        config = camera.get_config(context)
        cameraTimeAndDate = "Unknown"
        try:
            # find the date/time setting config item and get it
            # name varies with camera driver
            #   Canon EOS350d - 'datetime'
            #   PTP - 'd034'
            for name, fmt in (('datetime', '%Y-%m-%d %H:%M:%S'),
                              ('datetimeutc', None),
                              ('d034',     None)):
                OK, datetime_config = gp.gp_widget_get_child_by_name(config, name)
                if OK >= gp.GP_OK:
                    widget_type = gp.check_result(gp.gp_widget_get_type(datetime_config))
                    if widget_type == gp.GP_WIDGET_DATE:
                        raw_value = gp.check_result(
                            gp.gp_widget_get_value(datetime_config))
                        camera_time = datetime.fromtimestamp(raw_value)
                    else:
                        raw_value = gp.check_result(
                            gp.gp_widget_get_value(datetime_config))
                        if fmt:
                            camera_time = datetime.strptime(raw_value, fmt)
                        else:
                            camera_time = datetime.utcfromtimestamp(float(raw_value))
                    cameraTimeAndDate = camera_time.isoformat(' ')
                    break
        except Exception as e:
            app.logger.debug('Error reading camera time and date: ' + str(e))
            cameraTimeAndDate = "Unknown"   
        imgfmtselected, imgfmtoptions   = readRange (camera, context, 'imgsettings', 'imageformat')
        wbselected, wboptions           = readRange (camera, context, 'imgsettings', 'whitebalance')
        isoselected, isooptions         = readRange (camera, context, 'imgsettings', 'iso')
        apselected, apoptions           = readRange (camera, context, 'capturesettings', 'aperture')
        shutselected, shutoptions       = readRange (camera, context, 'capturesettings', 'shutterspeed')
        expselected, expoptions         = readRange (camera, context, 'capturesettings', 'exposurecompensation')

        gp.check_result(gp.gp_camera_exit(camera))
        cameraData['cameraDate']    = cameraTimeAndDate
        cameraData['focusmode']     = readValue (config, 'focusmode')
        cameraData['exposuremode']  = readValue (config, 'autoexposuremode')
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

    except gp.GPhoto2Error as e:
        flash(e.string)
        app.logger.debug('Camera GET error: ' + e.string)
    except Exception as e:
        app.logger.debug('Unknown camera GET error:' + str(e))
        
    templateData = cameraData.copy()
    return render_template('camera.html', **templateData)


@app.route("/camera", methods = ['POST'])    # The camera's POST method
@login_required
def cameraPOST():
    """ This page is where you manage all the camera settings."""
    try:
        camera = gp.Camera()
        context = gp.gp_context_new()
        camera.init(context)
        config = camera.get_config(context)

        if request.form['CamSubmit'] == 'apply':
            app.logger.debug('-- Camera Apply selected')
            #This *does* write a new setting to the camera:
            node = config.get_child_by_name('imageformat') #
            node.set_value(str(request.form.get('img')))
            # Don't bother sending any of the "read only" settings:
            if (request.form.get('wb') != None):
                node = config.get_child_by_name('whitebalance')
                node.set_value(str(request.form.get('wb')))
            if (request.form.get('iso') != None):
                node = config.get_child_by_name('iso')
                node.set_value(str(request.form.get('iso')))
            if (request.form.get('aperture') != 'implicit auto'):
                node = config.get_child_by_name('aperture')
                node.set_value(str(request.form.get('aperture')))
            if (request.form.get('shutter') != "auto"):
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
            return redirect(url_for('camera', preview=1))

    except gp.GPhoto2Error as e:
        app.logger.debug('Camera POST error: ' + e.string)
        flash(e.string)
    except Exception as e:
        app.logger.debug('Unknown camera POST error:' + str(e))

    return redirect(url_for('camera'))


@app.route("/intervalometer")
@login_required
def intervalometer():
    """ This page is where you manage all the interval settings for the Arduino."""

    templateData = {
        'piDoW' : '',
        'piStartHour' : '',
        'piEndHour' : '',
        'piInterval' : '',
        'availableShots': 'Unknown'
    }
    app.logger.debug('This is a GET to Intervalometer')

    # Camera comms:
    try:
        camera = gp.Camera()
        context = gp.gp_context_new()
        camera.init(context)
        config = camera.get_config(context)
        templateData['availableShots'] = readValue (config, 'availableshots')
        gp.check_result(gp.gp_camera_exit(camera))
    except gp.GPhoto2Error as e:
        flash(e.string)
        app.logger.debug('GPhoto camera error in intervalometer:' + str(e))
    except Exception as e:
        app.logger.debug('Unknown camera error in intervalometer:' + str(e))

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
    args = request.args.to_dict()
    if args.get('copyNow'):
        app.logger.debug('Detected /transfer/copyNow')
        copyNow()
        return redirect(url_for('main')) #If we transfer OK, return to main
    if not os.path.exists(iniFile):
        createConfigFile(iniFile)
    # Initialise the dictionary:
    templateData = {
        'tfrMethod'          : 'Off',    # Hides all options if the file isn't found or is bad
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
        'copyDay'            : '',
        'copyHour'           : '',
        'wakePiTime'         : '25',
        'piTransferLogLink'  : PI_TRANSFER_LINK
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
            app.logger.debug('Exception clearing piTransfer.log:' + str(e))

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
            app.logger.debug('INI file error writing:' + str(e))
            if 'Permission denied' in str(e):
                flash('Permission denied writing to the ini file')
            else:
                flash('Error writing to the Ini file')

    return redirect(url_for('transfer'))

  
@app.route("/copyNow")
def name():
    """
    This 'page' is only one of two called without the "@login_required" decorator. It's only called by 
    the cron job/script and will only execute if the calling IP is itself/localhost.
    """
    sourceIp = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if sourceIp != "127.0.0.1":
        abort(403)
    copyNow()
    res = make_response("")
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
        'piThumbCount'   : '80',
        'arduinoDate'    : 'Unknown',
        'arduinoTime'    : 'Unknown',
        'piUptime'       : 'Unknown',
        'piModel'        : 'Unknown',
        'piLinuxVer'     : 'Unknown',
        'piSpaceFree'    : 'Unknown',
        'wakePiTime'     : '',
        'wakePiDuration' : '',
        'rebootSafeWord' : REBOOT_SAFE_WORD
        }

    if not os.path.exists(iniFile):
        createConfigFile(iniFile)
    config = configparser.ConfigParser()
    config.read(iniFile)
    try:
        templateData['piThumbCount'] = config.get('Global', 'thumbsCount')
    except Exception as e:
        app.logger.debug('INI file error reading:' + str(e))
        templateData['piThumbCount'] = '20'

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

    try:
        templateData['piUptime']    = getPiUptime()
        templateData['piSpaceFree'] = getDiskSpace()
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
        app.logger.debug('Yes we got the SyncSystem button & value ' + str(request.form.get('SyncSystem')))
        writeString("ST=" + str(request.form.get('SyncSystem'))) # Send the new time and date to the Arduino

    if 'Reboot' in request.form:
        if str(request.form.get('rebootString')) == REBOOT_SAFE_WORD:
            writeString("RA")
            #app.logger.debug('Yes we got reboot safe word - ' + REBOOT_SAFE_WORD)
        else:
            pass
            #app.logger.debug('Button pressed but no reboot safe word - ' + REBOOT_SAFE_WORD)

    return redirect(url_for('system'))



def readValue ( camera, attribute ):
    """ Reads a simple attribute in the camera and returns the value """
    try:
        object = gp.check_result(gp.gp_widget_get_child_by_name(camera, attribute))
        value = gp.check_result(gp.gp_widget_get_value(object))
    except:
        value = '<Error>'
    return value


def readRange ( camera, context, group, attribute ):
    """
    Reads an attribute within a given group and returns the current setting and all the possible options
    It's only called by "camera", so in that context we already have an established connection to the
    camera, so it's inappropriate (and inefficient) to attempt a reconnection here.
    """
    options = []
    currentValue = ''
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
    except:
        app.logger.debug('readRange Threw')
    return currentValue, options


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


def copy_files(camera):
    """ Straight from Jim's examples again """
    if not os.path.isdir(PI_PHOTO_DIR):
        os.makedirs(PI_PHOTO_DIR)
    computer_files = list_Pi_Images(PI_PHOTO_DIR)
    camera_files = list_camera_files(camera)
    if not camera_files:
        app.logger.debug('No files found')
        return 1
    app.logger.debug('Copying files...')

    for path in camera_files:
        sourceFolderTree, imageFileName = os.path.split(path)
        dest = CreateDestPath(sourceFolderTree, PI_PHOTO_DIR)
        dest = os.path.join(dest, imageFileName)
        if dest in computer_files:
            continue
        app.logger.debug('Copying {0} --> {1}'.format(path, dest))
        camera_file = gp.check_result(gp.gp_camera_file_get(
            camera, sourceFolderTree, imageFileName, gp.GP_FILE_TYPE_NORMAL))
        gp.check_result(gp.gp_file_save(camera_file, dest))
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
        disk_total = disk.total / 2**30     # GiB.
        disk_used = disk.used / 2**30
        disk_free = str(round(disk.free / 2**30,2)) + ' GB'
    except:
        disk_free = "Unknown"
    return disk_free


def createConfigFile(iniFile):
    """ Thank you https://www.blog.pythonlibrary.org/2013/10/25/python-101-an-intro-to-configparser/ """
    try:
        config = configparser.ConfigParser()
        config.add_section('Global')
        config.set('Global', 'file created', time.strftime("%0d %b %Y",time.localtime(time.time())))
        config.set('Global', 'thumbscount', '20')
        config.add_section('Transfer')
        config.set('Transfer', 'tfrMethod', 'Off')
        config.add_section('Copy')
        with open(iniFile, 'w') as config_file:
            config.write(config_file)
    except:
        app.logger.debug('createConfigFile Threw creating ' + iniFile)
    return


def copyNow():
    writeString("WC") # Sends the WAKE command to the Arduino (just in case)
    time.sleep(1);    # (Adds another second on top of the 0.5s baked into WriteString)
    try:
        camera = gp.Camera()
        context = gp.gp_context_new()
        camera.init(context)
        copy_files(camera)
        gp.check_result(gp.gp_camera_exit(camera))
    except gp.GPhoto2Error as e:
        flash(e.string)
        app.logger.debug("Transfer wasn't able to connect to the camera: " + e.string)
    except Exception as e:
        app.logger.debug('Unknown error in copyNow: ' + str(e))
    return


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


#This always needs to be at the end, as nothing else will run after it - it's blocking:
if __name__ == "__main__":
   app.run(host='0.0.0.0')
