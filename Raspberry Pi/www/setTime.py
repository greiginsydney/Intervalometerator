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
#
# Thank you https://docs.python.org/2/howto/urllib2.html
#
# This script is executed every time the Pi boots. It reads the Arduino's time and sets same in the Pi (as the 
#  Pi's time is volatile - it's lost every time it powers-off).
# It runs BEFORE the cameraTransfer.py script.


from urllib.request import urlopen
from urllib.error import URLError
from datetime import datetime
import logging
import os
import re
import subprocess
import sys

LOGFILE_PATH = os.path.expanduser('/home/pi')
LOGFILE_NAME = os.path.join(LOGFILE_PATH, 'setTime.log')

htmltext = ''
newTime = 'Unknown'


def main(argv):
    logging.basicConfig(filename=LOGFILE_NAME, filemode='a', format='{asctime} {message}', style='{', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    log('')
    # If the 'midnight' flag is set, do NOT run if the systemd-timesyncd is active (as this means NTP controls the Pi's RTC)
    try:
        if sys.argv[1] == 'midnight':
            try:
                cmd = ['systemctl', 'is-active', 'systemd-timesyncd']
                result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, encoding='utf-8')
                (stdoutdata, stderrdata) = result.communicate()
                if stdoutdata:
                    stdoutdata = stdoutdata.strip()
                    if stdoutdata == 'active':
                        log('systemd-timesyncd = ' + str(stdoutdata) + '. The Pi takes its time from NTP. Updating the Arduino to follow Pi time')
                        setArduinoDateTime()
                        return
                    else:
                        log('systemd-timesyncd = ' + str(stdoutdata) + '. The Pi does NOT take its time from NTP. setTime.py continuing')
                if stderrdata:
                    stderrdata = stderrdata.strip()
                    log('systemd-timesyncd error = ' + str(stderrdata) + '. setTime.py aborting')
                    return
            except Exception as e:
                log('Unhandled systemd-timesyncd error: ' + str(e) + '. setTime.py aborting')
                return
        getArduinoDateTime()
    except:
        log('Unhandled error in sys.argv: ' + str(e))


def getArduinoDateTime():
    retryCount = 0
    while True:
        try:
            response = urlopen('http://localhost:8080/getTime')
            log('Response code = ' + str(response.getcode()))
            htmltext = response.read().decode('utf-8')
            log('This is what I received:' + str(htmltext))
            tempTime = re.search(('id="dateTime">(.*)</div>'), htmltext)
            if tempTime != None:
                newTime = tempTime.group(1)
                log('New time is ' + newTime)
                if 'Unknown' not in newTime:
                    break
            else:
                log('Failed to detect the time')
        except URLError as e:
            if hasattr(e, 'reason'):
                log('URL error. Reason = ' + str(e.reason))
            elif hasattr(e, 'code'):
                log('URL error. Code = ' + str(e.code))
        except Exception as e:
            log('Unhandled web error: ' + str(e))
        retryCount += 1
        if retryCount == 3:
            break
        log('RETRYING')

    try:
        #convert it to a form the date command will accept: Incoming is "2018 Nov 29 21:58:00"
        if "Unknown" not in newTime:
            timeCommand = ['/bin/date', '--set=%s' % datetime.strptime(newTime,'%Y %b %d %H:%M:%S')]
            result = subprocess.Popen(timeCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, encoding='utf-8')
            (stdoutdata, stderrdata) = result.communicate()
            if stdoutdata:
                log('Result = ' + str(stdoutdata))
            if stderrdata:
                log('Error = ' + str(stderrdata))
        else:
            log('Failed to set time. newTime = ' + newTime)
    except Exception as e:
        log('Unhandled time error: ' + str(e))


def setArduinoDateTime():
    retryCount = 0
    while True:
        try:
            response = urlopen('http://localhost:8080/setArduinoDateTime')
            log('Response code = ' + str(response.getcode()))
            htmltext = response.read().decode('utf-8')
            log('This is what I received: ' + str(htmltext))
            responseText = re.search(('<p>Set Arduino datetime to (.*)</p>'), htmltext)
            if responseText != None:
                newTime = responseText.group(1)
                log('New Arduino time is ' + newTime)
                break
            else:
                log('Failed to set the time')
        except URLError as e:
            if hasattr(e, 'reason'):
                log('URL error. Reason = ' + str(e.reason))
            elif hasattr(e, 'code'):
                log('URL error. Code = ' + str(e.code))
        except Exception as e:
            log('Unhandled web error: ' + str(e))
        retryCount += 1
        if retryCount == 3:
            break
        log('RETRYING')


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        #print 'error:' + str(e)
        pass


if __name__ == '__main__':
    main(sys.argv[1:])
