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
# https://greiginsydney.com/Intervalometerator
# https://intvlm8r.com


# Thank you https://docs.python.org/2/howto/urllib2.html
#
# This script is executed every time the Pi boots, causing it to trigger a sync with the camera.
# A pre-req task is that the Arduino has woken the camera, which we assume has taken place by the time the script runs.

from urllib2 import urlopen, URLError
import os

logfilepath = os.path.expanduser('/home/pi/')
logfilename = os.path.join(logfilepath, 'cameraTransfer.log')

htmltext = ''
resultcode = ''

try:
    response = urlopen('http://localhost/transfer?copyNow=1')
    resultcode = str(response.getcode())
    htmltext = response.read()
except URLError as e:
    if hasattr(e, 'reason'):
        resultcode = str(e.reason)
    elif hasattr(e, 'code'):
        resultcode = str(e.code)


try:
    # 'w' creates a new file each time, else 'a' to append.
    # I went with 'w' so I don't need to worry about the size of the file growing too large (or managing same).
    with open(logfilename, 'w') as logfile:
        logfile.write(resultcode + '\n')
        logfile.write('=========================\n')
        logfile.write(htmltext + '\n')
        logfile.write('=========================\n')
        logfile.close()
except Exception as e:
    #print 'error:' + str(e)
    pass
