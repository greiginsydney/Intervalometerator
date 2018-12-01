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
#
#
# Thank you https://docs.python.org/2/howto/urllib2.html
#
# This script is executed every time the Pi boots. It reads the Arduino's time and sets same in the Pi (as the 
#  Pi's time is volatile - it's lost every time it powers-off).
# It runs BEFORE the cameraTransfer.py script.


from urllib2 import urlopen, URLError
from datetime import datetime
import os
import re

logfilepath = os.path.expanduser('/home/pi/')
logfilename = os.path.join(logfilepath, 'setTime.log')

htmltext = ''
resultcode = ''
newTime = 'Unknown'

try:
    response = urlopen('http://localhost/')
    resultcode = str(response.getcode())
    htmltext = response.read()
    tempTime = re.search(('id="dateTime">(.*)</div>'), htmltext)
    if tempTime != None:
        newTime = tempTime.group(1)
    else:
        pass

except URLError as e:
    if hasattr(e, 'reason'):
        resultcode = str(e.reason)
    elif hasattr(e, 'code'):
        resultcode = str(e.code)

try:
    #convert it to a form the date command will accept: Incoming is "2018 Nov 29 21:58:00"
    if newTime != "Unknown":
        os.system('sudo date --set="%s"' % datetime.strptime(newTime, '%Y %b %d %H:%M:%S' ))
except Exception as e:
    resultcode = str(e)
     
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
