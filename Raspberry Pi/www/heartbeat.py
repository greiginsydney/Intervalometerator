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
# This project incorporates code from python-gphoto2, and we are incredibly indebted to Jim Easterbrook for it.
# python-gphoto2 - Python interface to libgphoto2 http://github.com/jim-easterbrook/python-gphoto2 Copyright (C) 2015-17 Jim
# Easterbrook jim@jim-easterbrook.me.uk


from datetime import datetime
import configparser # for the ini file
import logging
import os
import requests


# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

PI_USER_HOME     = os.path.expanduser("~")
INIFILE_DIR      = os.path.join(PI_USER_HOME, 'www')
INIFILE_NAME     = os.path.join(INIFILE_DIR, 'intvlm8r.ini')
LOGFILE_NAME     = os.path.join(PI_USER_HOME, 'heartbeat.log')
INTERNAL_HB_URL  = "http://localhost:8080/heartbeat"


def main():
    logging.basicConfig(filename=LOGFILE_NAME, filemode='a', format='{asctime} {message}', style='{', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    if not os.path.isfile(INIFILE_NAME):
        log("Heartbeat aborted. I've lost the INI file")
        return
    config = configparser.ConfigParser(
        {
            'heartbeaturl'       : '',
            'heartbeatfrequency' : ''
        })
    config.read(INIFILE_NAME)
    try:
        hbUrl  = config.get('Monitoring', 'heartbeaturl')
        hbFreq = config.get('Monitoring', 'heartbeatfrequency')
    except Exception as e:
        hbFreq = 'Off' # If we hit an unknown exception, force hbFreq=Off, because we can't be sure what triggered the error
        log('INI file error: ' + str(e))

    if (hbFreq == 'Off'):
        log('Heartbeat aborted. hbFreq=Off')
        return
    if not hbUrl:
        log('Heartbeat aborted. hbUrl=None')
        return
    now = datetime.now().minute
    hbNow = False
    if hbFreq == '60':
        if now == 30: hbNow = True
    elif hbFreq == '30':
        if (now == 15 or now == 45): hbNow = True
    elif (now + 60) % int(hbFreq) == 0: hbNow = True
    if hbNow == True:
        #The above code validates we're MEANT to be sending a heartbeat now.
        #The below calls the main intvlm8r script and gets *it* to initiate the heartbeat to the monitoring URL
        #(The point being we won't send a HB probe if the *intvlm8r* script isn't running OK)
        initiateHeartbeat(INTERNAL_HB_URL)
    else:
        log(f"Not yet Heartbeat o'clock. hbFreq={hbFreq}")


def initiateHeartbeat(url):
    """
    This fn pings the heartbeat URL and logs the result to the LOGFILE_NAME file
    """
    response = None
    statusCode = 0
    if url:
        htmltext = None
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status() #Throws a HTTPError if we didn't receive a 2xx response
            htmltext = response.text.rstrip()
            statusCode = response.status_code
            log(f'Status code = {statusCode}')
            log(f'This is what I received: {htmltext}')
        except requests.exceptions.Timeout as e:
            log(f'initiateHeartbeat() Timeout error: {e}')
        except requests.exceptions.ConnectionError as e:
            log(f'initiateHeartbeat() ConnectionError: {e}')
        except requests.exceptions.HTTPError as e:
            log(f'initiateHeartbeat() HTTPError: {e}')
        except requests.exceptions.TooManyRedirects as e:
            log(f'initiateHeartbeat() TooManyRedirects error: {e}')
        except Exception as e:
            log(f'initiateHeartbeat() Unhandled web error: {e}')
    else:
        log(f'initiateHeartbeat() exited. No heartbeatUrl')
    return statusCode


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        print(f'error: {e}')
        #pass


if __name__ == '__main__':
    main()
