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

# This script is executed every time the Pi boots, causing it to trigger a sync with the camera.
# A pre-req task is that the Arduino has woken the camera, which we assume has taken place by the time the script runs.

import configparser # for the ini file
import datetime
import logging
import os
import requests
import sys
import time

# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

sudo_username = os.getenv("SUDO_USER")
if sudo_username:
    PI_USER_HOME = os.path.expanduser('~' + sudo_username + '/')
else:
    PI_USER_HOME = os.path.expanduser('~')

LOGFILE_NAME = os.path.join(PI_USER_HOME, 'cameraTransfer.log')
INIFILE_NAME = os.path.join(PI_USER_HOME, 'www/intvlm8r.ini')

htmltext = ''


def main(argv):
    logging.basicConfig(filename=LOGFILE_NAME, filemode='a', format='{asctime} {message}', style='{', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    log('')
    log(f'sys.argv = {sys.argv}')
    copyNow = False
    bootup  = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'copyNow':
            copyNow = True
        elif sys.argv[1] == 'bootup':
            bootup = True

    if not os.path.exists(INIFILE_NAME):
        pass
    config = configparser.ConfigParser(
        {
        'copyDay'         : 'Off',
        'copyHour'        : '00',
        'copyOnBootup'    : False,
        'wakePiHour'      : '25',
        'enableCameraUsb' : True
        })
    config.read(INIFILE_NAME)
    try:
        copyDay         = config.get('Copy', 'copyDay')
        copyHour        = config.get('Copy', 'copyHour')
        copyOnBootup    = config.getboolean('Copy', 'copyOnBootup')
        wakePiHour      = config.get('Global', 'wakePiHour')
        enableCameraUsb = config.getboolean('Global', 'enableCameraUsb')

    except Exception as e:
        copyDay = 'Off' # If we hit an exception, force copyDay=Off
        copyHour = '00'
        copyOnBootup = False
        wakePiHour = 25
        enableCameraUsb = True
        log('INI file error: ' + str(e))

    now = datetime.datetime.now()
    log(f'Now values are: NowDay = {now.strftime("%A")}, NowHour = {now.strftime("%H")}, CopyDay = {copyDay} , CopyHour = {copyHour}. wakePiHour is {wakePiHour}:00')
    if enableCameraUsb == False:
        log('Not OK to copy: enableCameraUsb is False')
        return
    if copyNow == True:
        # We're OK to copy NOW. (copyNow trumps all other options)
        log('OK to copy on copyNow')
    elif (((now.strftime("%A") == copyDay) | (copyDay == "Daily")) & ((now.strftime("%H") == wakePiHour ) | (now.strftime("%H") == copyHour))):
        # Now is a valid combo of day & hour
        log(f'OK to copy @ {now.strftime("%H")}:00 on {now.strftime("%A")}')
    elif bootup == True:
        if copyOnBootup == True:
            # We're OK to copy NOW, as we've been called by the service and the bootup flag has been set
            log('OK to copy on bootup')
        else:
            log('Script ran at bootup but flag not set. Exiting')
            return
    else:
        log('Not OK to copy')
        return

    response = None
    statusCode = 0
    htmltext = None
    try:
        response = requests.get('http://localhost:8080/copyNow', timeout=30)
        response.raise_for_status() #Throws a HTTPError if we didn't receive a 2xx response
        htmltext = response.text.rstrip()
        statusCode = response.status_code
        log(f'Status code = {statusCode}')
        log(f'This is what I received: {htmltext}')
    except requests.exceptions.Timeout as e:
        log(f'Timeout error: {e}')
    except requests.exceptions.ConnectionError as e:
        log(f'ConnectionError: {e}')
    except requests.exceptions.HTTPError as e:
        log(f'HTTPError: {e}')
    except requests.exceptions.TooManyRedirects as e:
        log(f'TooManyRedirects error: {e}')
    except Exception as e:
        log(f'Unhandled web error: {e}')


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        #print(f'error: {e}')
        pass


if __name__ == '__main__':
    main(sys.argv[1:])
