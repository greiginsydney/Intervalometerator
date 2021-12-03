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
    LOGFILE_PATH = os.path.expanduser('~' + sudo_username + '/')
else:
    LOGFILE_PATH = os.path.expanduser('~')
LOGFILE_NAME = os.path.join(LOGFILE_PATH, 'cameraTransfer.log')
INIFILE_PATH = os.path.expanduser('~')
INIFILE_NAME = os.path.join(INIFILE_PATH, 'www/intvlm8r.ini')

htmltext = ''


def main(argv):
    logging.basicConfig(filename=LOGFILE_NAME, filemode='w', format='{asctime} {message}', style='{', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    copyNow = False
    try:
        if sys.argv[1] == 'copyNow':
            copyNow = True
    except:
        pass

    if not os.path.exists(INIFILE_NAME):
        pass
    config = configparser.ConfigParser(
        {
        'copyDay'         : 'Off',
        'copyHour'        : '00',
        })
    config.read(INIFILE_NAME)
    try:
        copyDay       = config.get('Copy', 'copyDay')
        copyHour      = config.get('Copy', 'copyHour')

    except Exception as e:
        copyDay = 'Off' # If we hit an exception, force copyDay=Off
        copyHour = '00'
        log('INI file error: ' + str(e))

    log('')
    now = datetime.datetime.now()
    log(f'Now values are: NowDay = {now.strftime("%A")}, NowHour = {now.strftime("%H")}, CopyDay = {copyDay} , CopyHour= {copyHour}')
    if ((now.strftime("%A") == copyDay) | (copyDay == "Daily")):
        # We're OK to copy TODAY
        if (copyNow == True):
            # We're OK to copy NOW
            log('OK to copy on copyNow.')
        elif (now.strftime("%H") == copyHour):
            # We're OK to copy NOW
            log(f'OK to copy @ {copyHour}:00.')
        else:
            log(f'Not OK to copy @ {now.strftime("%H")}:00.')
            return
    else:
        log(f'Not OK to copy today ({now.strftime("%A")}).')
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
