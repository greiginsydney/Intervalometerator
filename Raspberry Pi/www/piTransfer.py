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
# SFTP code from the paramiko project: https://github.com/paramiko/paramiko


import datetime
from ftplib import FTP
import ConfigParser # for the ini file
import dropbox
import fileinput
import logging
import os
import paramiko
import re    #RegEx
import socket
import sys
import time


# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

PI_PHOTO_DIR  = os.path.expanduser('/home/pi/photos')
UPLOADED_PHOTOS_LIST = os.path.join(PI_PHOTO_DIR, "uploadedOK.txt")
INIFILE_PATH = os.path.expanduser('/home/pi')
INIFILE_NAME = os.path.join(INIFILE_PATH, 'www/intvlm8r.ini')
LOGFILE_DIR = os.path.expanduser('/home/pi/www/static')
LOGFILE_NAME = os.path.join(LOGFILE_DIR, 'piTransfer.log')

# Paramiko client configuration
UseGSSAPI = True  # enable GSS-API / SSPI authentication
DoGSSAPIKeyExchange = True
Port = 22


def main(argv):
    logging.basicConfig(filename=LOGFILE_NAME, filemode='a', format='%(asctime)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    copyNow = False
    try:
        if sys.argv[1] == 'copyNow':
            copyNow = True
    except:
        pass
    
    if not os.path.exists(INIFILE_NAME):
        pass
    config = ConfigParser.SafeConfigParser(
        {
        'tfrmethod'         : 'Off',
        'ftpServer'         : '',
        'ftpUser'           : '',
        'ftpPassword'       : '',
        'sftpServer'        : '',
        'sftpUser'          : '',
        'sftpPassword'      : '',
        'sftpRemoteFolder'  : '',
        'dbx_token'         : '',
        'transferDay'       : '',
        'transferHour'      : '',
        })
    config.read(INIFILE_NAME)
    try:
        tfrMethod         = config.get('Transfer', 'tfrmethod')
        ftpServer         = config.get('Transfer', 'ftpServer')
        ftpUser           = config.get('Transfer', 'ftpUser')
        ftpPassword       = config.get('Transfer', 'ftpPassword')
        sftpServer        = config.get('Transfer', 'sftpServer')
        sftpUser          = config.get('Transfer', 'sftpUser')
        sftpPassword      = config.get('Transfer', 'sftpPassword')
        sftpRemoteFolder  = config.get('Transfer', 'sftpRemoteFolder')
        dbx_token         = config.get('Transfer', 'dbx_token')
        transferDay       = config.get('Transfer', 'transferDay')
        transferHour      = config.get('Transfer', 'transferHour')

    except Exception as e:
        tfrMethod = "Off"
        log('INI file error:' + str(e))

    while '//' in sftpRemoteFolder:
        sftpRemoteFolder = sftpRemoteFolder.replace('//', '/')

    now = datetime.datetime.now()
    if (((now.strftime("%A") == transferDay) | (transferDay == "Daily")) & (now.strftime("%H") == transferHour)):
        # We're OK to transfer now
        log('OK to transfer @ %s:00. Method = %s' % (transferHour, tfrMethod))
    elif copyNow == True:
        # We're OK to transfer now
        log("OK to transfer on 'copyNow'. Method = %s" % tfrMethod)
    else:
        log('Not OK to transfer. Method = %s' % tfrMethod)
        return
    if (tfrMethod == 'FTP'):
        commenceFtp(ftpServer, ftpUser, ftpPassword)
    elif (tfrMethod == 'SFTP'):
        commenceSftp(sftpServer, sftpUser, sftpPassword, sftpRemoteFolder)
    elif (tfrMethod == 'Dropbox'):
        commenceDbx(dbx_token)


def list_New_Images(imagesPath, previouslyUploadedFile):
    currentlist = []
    lastlist = []
    newFiles = []
    for root, dirs, files in os.walk(os.path.expanduser(imagesPath)):
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
            currentlist.append(os.path.join(root, name))
    
    for line in fileinput.input(previouslyUploadedFile):
        lastlist.append(line.rstrip("\n"))
    newFiles = list(set(currentlist) - set(lastlist))
    return newFiles


def makeShortPath(remoteRootFolder, filepath):
    shortPath = re.search(("DCIM/\S*"), filepath)
    if (shortPath != None):
        destFilePath = os.path.join(remoteRootFolder, shortPath.group(0))
    else:
         destFilePath = os.path.join(remoteRootFolder, filepath)
    return destFilePath


def commenceFtp(ftpServer, ftpUser, ftpPassword):
    ftp = FTP()
    ftp.set_debuglevel(2)
    try:
        ftp.connect(ftpServer, 21)
    except Exception as e:
        if 'No route to host' in e:
            log('ftp connect exception: no route to host. Bad IP address or hostname')
        elif 'Connection timed out' in e:
            log('ftp connect exception: connection timed out. Destination valid but not listening on port 21')
        else:
            log('ftp login exception. Unknown error: ' + str(e))
        return
    try:
        ftp.login(ftpUser,ftpPassword)
    except Exception as e:
        if 'Login or password incorrect' in e:
            log('ftp login exception: Login or password incorrect')
        else:
            log('ftp login exception. Unknown error: ' + str(e))
        return
    ftp.set_pasv(False) #Filezilla Server defaults to passive, and 2x passive = nothing happens!

    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    if len(newFiles) == 0:
        log("No files need to be uploaded")
    else:
        for needupload in newFiles:
            log("Uploading " + needupload)
            # Format the destination path to strip the /home/pi/photos off:
            shortPath = makeShortPath('', needupload)
            ftp_upload(ftp, needupload, shortPath)
            with open(UPLOADED_PHOTOS_LIST, "a") as myfile:
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


def commenceDbx(token):
    try:
        dbx = dropbox.Dropbox(token)
    except Exception as e:
        log('Exception signing in to Dropbox: ' + str(e))
        return
    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    if len(newFiles) == 0:
        log("No files need to be uploaded")
    else:
        for needupload in newFiles:
            log("Uploading " + needupload)
            # Format the destination path to strip the /home/pi/photos off:
            shortPath = makeShortPath('', needupload)
            path,filename = os.path.split(shortPath)
            result = dbx_upload(dbx, needupload, path, '', filename)
            if result == None:
                log('Error uploading ' + needupload)
            else:
                with open(UPLOADED_PHOTOS_LIST, "a") as myfile:
                    myfile.write(needupload + "\n")


def dbx_upload(dbx, fullname, folder, subfolder, name, overwrite=True):
    """Upload a file.
    Return the request response, or None in case of error.
    """
    path = '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    while '//' in path:
        path = path.replace('//', '/')
    mode = (dropbox.files.WriteMode.overwrite
            if overwrite
            else dropbox.files.WriteMode.add)
    mtime = os.path.getmtime(fullname)
    with open(fullname, 'rb') as f:
        data = f.read()
    try:
        res = dbx.files_upload(
            data, path, mode,
            client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
            mute=True)
    except dropbox.exceptions.ApiError as err:
        log('Dropbox API error' + err)
        return None
    #log('Dropbox uploaded as ' + res.name.encode('utf8'))
    #log('Dropbox result = ' + str(res))
    return res


def commenceSftp(sftpServer, sftpUser, sftpPassword, sftpRemoteFolder):
    # get host key, if we know one
    hostkeytype = None
    hostkey = None
    try:
        host_keys = paramiko.util.load_host_keys(
            os.path.expanduser("~/.ssh/known_hosts")
        )
        log('*** we made it to here without throwing an error')
    except IOError:
        log('*** Unable to open host keys file')
        host_keys = {}

    if sftpServer in host_keys:
        hostkeytype = host_keys[sftpServer].keys()[0]
        hostkey = host_keys[sftpServer][hostkeytype]
        log("Using host key of type %s" % hostkeytype)
    else:
        log("No host keys found")

    # now, connect and use paramiko Transport to negotiate SSH2 across the connection
    try:
        t = paramiko.Transport((sftpServer, Port))
        t.connect(
            hostkey,
            sftpUser,
            sftpPassword,
            gss_host=socket.getfqdn(sftpServer),
            gss_auth=False, #gss_auth=UseGSSAPI,
            gss_kex=False, #gss_kex=DoGSSAPIKeyExchange,
        )
        sftp = paramiko.SFTPClient.from_transport(t)
    except paramiko.AuthenticationException as e:
        log('Authentication failed: ' + str(e))
        return
    except paramiko.SSHException as e:
        log('Unable to establish SSH connection: ' + str(e))
        return
    except paramiko.BadHostKeyException as e:
        log("Unable to verify server's host key: " + str(e))
        return
    except Exception as e:
        log('Exception signing in to SFTP server: ' + str(e))
        return

    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    if len(newFiles) == 0:
        log("No files need to be uploaded")
    else:
        previousFilePath = ''
        for needupload in newFiles:
            log("Uploading " + needupload)
            # Format the destination path to strip the /home/pi/photos off:
            shortPath = makeShortPath(sftpRemoteFolder, needupload)
            try:
                remoteFolderTree = os.path.split(shortPath)
                if previousFilePath != remoteFolderTree[0]:
                    # Create the tree & CD to it:
                    foldersList = remoteFolderTree[0].split("/")
                    remotePath = "/"
                    if len(foldersList) != 0:
                        for oneFolder in foldersList:
                            remotePath += oneFolder + "/"
                            try:
                                sftp.chdir(remotePath)
                            except IOError:
                                sftp.mkdir(oneFolder)
                                sftp.chdir(remotePath)
                sftp.put(needupload, remoteFolderTree[1])
                previousFilePath = remoteFolderTree[0]
                with open(UPLOADED_PHOTOS_LIST, "a") as myfile:
                    myfile.write(needupload + "\n")
            except Exception as e:
                log('Error uploading ' + str(e))
    sftp.close()
    t.close()


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        print 'error:' + str(e)
        #pass


if __name__ == '__main__':
    main(sys.argv[1:])
