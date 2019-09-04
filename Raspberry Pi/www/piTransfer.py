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

# This script is based on the FTP example from http://makble.com/upload-new-files-to-ftp-server-with-python


from datetime import datetime
from ftplib import FTP 
import ConfigParser # for the ini file
import fileinput
import logging
import os
import re    #RegEx


# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

PI_PHOTO_DIR  = os.path.expanduser('/home/pi/photos')
LOGFILE_PATH = os.path.expanduser('/home/pi')
LOGFILE_NAME = os.path.join(LOGFILE_PATH, 'piTransfer.log')
#iniFile = os.path.join(app.root_path, 'intvlm8r.ini')
iniFile = os.path.join(LOGFILE_PATH, 'www/intvlm8r.ini')


def main():
    logging.basicConfig(filename=LOGFILE_NAME, filemode='a', format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    if not os.path.exists(iniFile):
        pass
    config = ConfigParser.SafeConfigParser(
        {
        'tfrmethod'     : 'Off',
        'ftpServer'     : '',
        'ftpUser'       : '',
        'ftpPassword'   : '',
        'fileServer'    : '',
        'fileUser'      : '',
        'filePassword'  : '',
        'transferDay'   : '',
        'transferHour'  : '',
        })
    config.read(iniFile)
    try:
        tfrMethod     = config.get('Transfer', 'tfrmethod')
        ftpServer     = config.get('Transfer', 'ftpServer')
        ftpUser       = config.get('Transfer', 'ftpUser')
        ftpPassword   = config.get('Transfer', 'ftpPassword')
        fileServer    = config.get('Transfer', 'fileServer')
        fileUser      = config.get('Transfer', 'fileUser')
        filePassword  = config.get('Transfer', 'filePassword')
        transferDay   = config.get('Transfer', 'transferDay')
        transferHour  = config.get('Transfer', 'transferHour')
        
    except Exception as e:
        tfrMethod = "Off"
        log('INI file error:' + str(e))

    
    now = datetime.now()
    if (((now.strftime("%A") == transferDay) | (transferDay == "Daily")) & (now.strftime("%H") == transferHour)):
        # We're OK to transfer now
        log('OK to transfer at ' + (now.strftime("%H:%M:%S on %d %b %Y")))
    else:    
        log('Not OK to transfer at ' + (now.strftime("%H:%M:%S on %d %b %Y")))
        return
    if (tfrMethod == 'FTP'):
        uploadFtp(ftpServer, ftpUser, ftpPassword)


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
                # Don't try to upload the/any .txt files
                continue
            result.append(os.path.join(root, name))
    return result


def uploadFtp(ftpServer, ftpUser, ftpPassword):
    ftp = FTP()
    ftp.set_debuglevel(2)
    try:
        ftp.connect(ftpServer, 21)
    except Exception as e:
        if 'No route to host' in e:
            log('ftp connect exception: no route to host. Bad IP address or hostname'
        else if 'Connection timed out' in e:
            log('ftp connect exception: connection timed out. Destination valid but not listening on port 21'
        else:
            log('ftp login exception. Unknown error: ' + str(e))
        return
    try:
        ftp.login(ftpUser,ftpPassword)
    except Exception as e:
        if 'Login or password incorrect' in e:
            log('ftp login exception: Login or password incorrect'
        else:
            log('ftp login exception. Unknown error: ' + str(e))
        return
    ftp.set_pasv(False)
    lastlist = []
    for line in fileinput.input(os.path.join(PI_PHOTO_DIR, "uploadedOK.txt")):
        lastlist.append(line.rstrip("\n"))
    currentlist = list_Pi_Images(PI_PHOTO_DIR)
    newfiles = list(set(currentlist) - set(lastlist))
    if len(newfiles) == 0:
        log("No files need to be uploaded")
    else:
        for needupload in newfiles:
            log("Uploading " + needupload)
            upload_img(ftp, needupload)
            with open(os.path.join(PI_PHOTO_DIR, "uploadedOK.txt"), "a") as myfile:
              myfile.write(needupload + "\n")
    ftp.quit()


def ftp_upload(ftp, localfile, remotefile):
    path,filename = os.path.split(remotefile)
    try:
        ftp.cwd(path)
    except:
        ftp.mkd(path)
    fp = open(localfile, 'rb')
    try:
        ftp.storbinary('STOR %s' % filename, fp, 1024)
    except Exception as e:
        fp.close()
        log('ftp_upload exception:' + str(e))
        path,filename = os.path.split(remotefile)
        log("creating directory: " + path)
        ftp.mkd(path)
        ftp_upload(ftp, localfile, remotefile)
        fp.close()
        return
    fp.close()
    log ('Successfully uploaded ' + localfile + ' to ' + remotefile)


def upload_img(ftp, piFile):
    # Format the destination path to strip the /home/pi/photos off:
    shortPath = re.search(("DCIM/\S*"), piFile)
    if (shortPath != None):
        destFile = "/" + str(shortPath.group(0))
    else:
        destFile = piFile
    ftp_upload(ftp, piFile, destFile)


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        print 'error:' + str(e)
        #pass


if __name__ == '__main__':
    main()
