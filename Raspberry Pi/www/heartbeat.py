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
from urllib.request import urlopen
from urllib.error import URLError
import configparser # for the ini file
import logging
import os


# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

PI_USER_HOME     = os.path.expanduser("~")
INIFILE_DIR      = os.path.join(PI_USER_HOME, 'www')
INIFILE_NAME     = os.path.join(INIFILE_DIR, 'intvlm8r.ini')
LOGFILE_NAME     = os.path.join(PI_USER_HOME, 'heartbeat.log')
PI_HBRESULT_FILE = os.path.join(PI_USER_HOME, 'hbresults.txt')
INTERNAL_HB_URL  = "http://localhost:8080/heartbeat"


def main():
    logging.basicConfig(filename=LOGFILE_NAME, filemode='w', format='{asctime} {message}', style='{', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    if not os.path.isfile(INIFILE_NAME):
        log("STATUS: Heartbeat aborted. I've lost the INI file")
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
    if (now + 60) % int(hbFreq) == 0:
        #The above code validates we're MEANT to be sending a heartbeat now.
        #The below calls the main intvlm8r script and gets *it* to initiate the heartbeat to the monitoring URL
        #(The point being we won't send a HB probe if the *intvlm8r* script isn't running OK)
        initiateHeartbeat(INTERNAL_HB_URL)
    else:
        print('not yet Heartbeat oclock')


def initiateHeartbeat(Url):
    """
    This fn pings the heartbeat URL and logs the result to the 'hbResult' file
    """
    statusCode = None
    if Url:
        htmltext = None
        try:
            with urlopen(Url) as response:
                htmltext = response.read()
                statusCode = response.getcode()
            log('Status code = {0}'.format(str(statusCode)))
            log('This is what I received: ' + str(htmltext))
        except URLError as e:
            if hasattr(e, 'reason'):
                log('initiateHeartbeat() URL error. Reason = ' + str(e.reason))
            elif hasattr(e, 'code'):
                log('initiateHeartbeat() URL error. Code = ' + str(e.code))
            else:
                log('initiateHeartbeat() Unknown URL error: ' + str(e))
        except socket.timeout as e:
            log('initiateHeartbeat() urlopen timed out : ' + str(e))
        except Exception as e:
            log('initiateHeartbeat() Unhandled web error: ' + str(e))
        try:
            with open(PI_HBRESULT_FILE, 'w') as resultFile:
                nowtime = datetime.now().strftime('%Y/%m/%d %H:%M:%S') #2019/09/08 13:06:03
                if statusCode:
                    resultFile.write('{0} ({1})'.format(nowtime, statusCode))
                else:
                    resultFile.write('{0} Error'.format(nowtime))
        except Exception as e:
            log('initiateHeartbeat() exception: ' + str(e))
    else:
        log('initiateHeartbeat() exited. No heartbeatUrl')
        print('no url')
    return statusCode


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        print('error: ' + str(e))
        #pass


if __name__ == '__main__':
    main()
