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
# Google Drive bits with thanks to @Jerbly: http://jeremyblythe.blogspot.com/2015/06/motion-google-drive-uploader-for-oauth.html
# Dropbox 2022: https://github.com/dropbox/dropbox-sdk-python/blob/main/example/oauth/commandline-oauth-pkce.py
#             & https://www.dropboxforum.com/t5/Dropbox-API-Support-Feedback/Oauth2-refresh-token-question-what-happens-when-the-refresh/td-p/486241


import datetime
from ftplib import FTP
import configparser # for the ini file
import fileinput
import logging
import os
import re    #RegEx
import socket
import subprocess
import sys
import time

#Only attempt to import these if they've been installed:
#(My attempts at lazy-loading and alternative test/load strategies failed.)
try:
    import dropbox
    from dropbox import DropboxOAuth2FlowNoRedirect
    from dropbox.exceptions import ApiError, AuthError
except:
    pass
try:
    import paramiko
except:
    pass
try:
    import sysrsync
except:
    pass
try:
    import httplib2
    from apiclient import discovery
    from oauth2client import client
    from oauth2client.file import Storage
    from googleapiclient.http import MediaFileUpload
except:
    pass

# ////////////////////////////////
# /////////// STATICS ////////////
# ////////////////////////////////

sudo_username = os.getenv("SUDO_USER")
if sudo_username:
    PI_USER_HOME = os.path.expanduser('~' + sudo_username + '/')
else:
    PI_USER_HOME = os.path.expanduser('~')

PI_PHOTO_DIR  = os.path.join(PI_USER_HOME, 'photos')
PI_THUMBS_DIR = os.path.join(PI_USER_HOME, 'thumbs')
PI_THUMBS_INFO_FILE  = os.path.join(PI_THUMBS_DIR, 'piThumbsInfo.txt')
PI_PREVIEW_DIR = os.path.join(PI_USER_HOME, 'preview')
UPLOADED_PHOTOS_LIST = os.path.join(PI_PHOTO_DIR, 'uploadedOK.txt')
INIFILE_DIR          = os.path.join(PI_USER_HOME, 'www')
INIFILE_NAME         = os.path.join(INIFILE_DIR, 'intvlm8r.ini')
LOGFILE_DIR          = os.path.join(PI_USER_HOME, 'www/static')
LOGFILE_NAME         = os.path.join(LOGFILE_DIR, 'piTransfer.log')
KNOWN_HOSTS_FILE     = os.path.join(PI_USER_HOME, '.ssh/known_hosts')
GOOGLE_CREDENTIALS   = os.path.join(PI_USER_HOME , 'www/Google_credentials.txt')
DROPBOX_TOKEN        = os.path.join(PI_USER_HOME , 'www/Dropbox_token.txt')

# Paramiko client configuration
sftpPort = 22


def main(argv):
    logging.basicConfig(filename=LOGFILE_NAME, filemode='a', format='{asctime} {message}', style='{', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    copyNow = False
    if len(sys.argv) > 1:
        if sys.argv[1] == 'copyNow':
            copyNow = True
        if sys.argv[1] == 'reauthGoogle':
            returncode = reauthGoogle()
            if returncode == 0:
                copyNow = True
            else:
                return 0

    global deleteAfterTransfer  #Made global instead of passing this down from here to all the nested functions.

    if not os.path.isfile(INIFILE_NAME):
        log("STATUS: Upload aborted. I've lost the INI file")
        return
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
        'dbx_app_key'        : '',
        'rsyncUsername'      : '',
        'rsyncHost'          : '',
        'rsyncRemoteFolder'  : '',
        'transferDay'        : '',
        'transferHour'       : '',
        'deleteAfterTransfer': False
        })
    config.read(INIFILE_NAME)
    try:
        tfrMethod           = config.get('Transfer', 'tfrmethod')
        ftpServer           = config.get('Transfer', 'ftpServer')
        ftpUser             = config.get('Transfer', 'ftpUser')
        ftpPassword         = config.get('Transfer', 'ftpPassword')
        ftpRemoteFolder     = config.get('Transfer', 'ftpRemoteFolder')
        sftpServer          = config.get('Transfer', 'sftpServer')
        sftpUser            = config.get('Transfer', 'sftpUser')
        sftpPassword        = config.get('Transfer', 'sftpPassword')
        sftpRemoteFolder    = config.get('Transfer', 'sftpRemoteFolder')
        googleRemoteFolder  = config.get('Transfer', 'googleRemoteFolder')
        dbx_app_key         = config.get('Transfer', 'dbx_app_key')
        rsyncUsername       = config.get('Transfer', 'rsyncUsername')
        rsyncHost           = config.get('Transfer', 'rsyncHost')
        rsyncRemoteFolder   = config.get('Transfer', 'rsyncRemoteFolder')
        transferDay         = config.get('Transfer', 'transferDay')
        transferHour        = config.get('Transfer', 'transferHour')
        deleteAfterTransfer = config.getboolean('Transfer', 'deleteAfterTransfer')

    except Exception as e:
        tfrMethod = 'Off' # If we hit an unknown exception, force tfrMethod=Off, because we can't be sure what triggered the error
        log(f'INI file error: {e}')

    if len(sys.argv) > 1:
        if sys.argv[1] == 'reauthDropbox':
            returncode = reauthDropbox(dbx_app_key)
            if returncode == 0:
                copyNow = True
            else:
                return 0

    if (tfrMethod == 'Off'):
        log('STATUS: Upload aborted. tfrMethod=Off')
        return

    log('')
    now = datetime.datetime.now()
    if (((now.strftime("%A") == transferDay) | (transferDay == "Daily")) & (now.strftime("%H") == transferHour)):
        # We're OK to transfer now
        log(f'OK to transfer @ {transferHour}:00. Method = {tfrMethod}')
    elif copyNow == True:
        # We're OK to transfer now
        log(f"OK to transfer on 'copyNow'. Method = {tfrMethod}")
    else:
        log(f'Not OK to transfer. Method = {tfrMethod}')
        return

    log(f'STATUS: Commencing upload using {tfrMethod}')
    if (tfrMethod == 'FTP'):
        while '\\' in ftpRemoteFolder:
            ftpRemoteFolder = ftpRemoteFolder.replace('\\', '/') # Escaping means the '\\' here is seen as a single backslash
        while '//' in ftpRemoteFolder:
            ftpRemoteFolder = ftpRemoteFolder.replace('//', '/')
        log(f'ftpServer={ftpServer}, ftpUser={ftpUser}, ftpPassword=<redacted>, ftpRemoteFolder={ftpRemoteFolder}')
        commenceFtp(ftpServer, ftpUser, ftpPassword, ftpRemoteFolder)
    elif (tfrMethod == 'SFTP'):
        while '\\' in sftpRemoteFolder:
            sftpRemoteFolder = sftpRemoteFolder.replace('\\', '/') # Escaping means the '\\' here is seen as a single backslash
        while '//' in sftpRemoteFolder:
            sftpRemoteFolder = sftpRemoteFolder.replace('//', '/')
        log(f'sftpServer={sftpServer}, sftpUser={sftpUser}, sftpPassword=<redacted>, sftpRemoteFolder={sftpRemoteFolder}')
        commenceSftp(sftpServer, sftpUser, sftpPassword, sftpRemoteFolder)
    elif (tfrMethod == 'Dropbox'):
        commenceDbx(dbx_app_key)
    elif (tfrMethod == 'Google Drive'):
        while '\\' in googleRemoteFolder:
            googleRemoteFolder = googleRemoteFolder.replace('\\', '/') # Escaping means the '\\' here is seen as a single backslash
        while '//' in googleRemoteFolder:
            googleRemoteFolder = googleRemoteFolder.replace('//', '/')
        commenceGoogle(googleRemoteFolder)
    elif (tfrMethod == 'rsync'):
        while '\\' in rsyncRemoteFolder:
            rsyncRemoteFolder = rsyncRemoteFolder.replace('\\', '/') # Escaping means the '\\' here is seen as a single backslash
        while '//' in rsyncRemoteFolder:
            rsyncRemoteFolder = rsyncRemoteFolder.replace('//', '/')
        log(f'rsyncUsername={rsyncUsername}, rsyncHost={rsyncHost}, rsyncRemoteFolder={rsyncRemoteFolder}')
        commenceRsync(rsyncUsername, rsyncHost, rsyncRemoteFolder)


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


def commenceFtp(ftpServer, ftpUser, ftpPassword, ftpRemoteFolder):
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftpPort = 21
    if ':' in ftpServer:
        ftpPort = int(ftpServer.split(':')[1])
        ftpServer = ftpServer.split(':')[0]
        log(f'ftpServer={ftpServer}, port={ftpPort}')
    try:
        ftp.connect(ftpServer, ftpPort)
    except Exception as e:
        if 'No route to host' in str(e):
            log('FTP connect exception: no route to host. Bad IP address or hostname')
        elif 'Connection timed out' in str(e):
            log('FTP connect exception: connection timed out. Destination valid but not listening on port 21')
        else:
            log(f'FTP login exception. Unknown error: {e}')
        log('STATUS: FTP connection failed')
        return
    try:
        ftp.login(ftpUser,ftpPassword)
    except Exception as e:
        if 'Login or password incorrect' in str(e):
            log('FTP login exception: Login or password incorrect')
        else:
            log(f'FTP login exception. Unknown error: {e}')
        log('STATUS: FTP login failed')
        return
    ftp.set_pasv(False) #Filezilla Server defaults to passive, and 2x passive = nothing happens!

    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    numNewFiles = len(newFiles)
    if numNewFiles == 0:
        log('STATUS: No new files to upload')
    else:
        numFilesOK = 0
        previousFilePath = ''
        for needupload in newFiles:
            for retries in range(2):
                log(f'Uploading {needupload}')
                # Format the destination path to strip the /home/pi/photos off:
                shortPath = makeShortPath(ftpRemoteFolder, needupload)
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
                                    ftp.cwd(remotePath)
                                except:
                                    ftp.mkd(oneFolder)
                                    ftp.cwd(remotePath)
                    fp = open(needupload, 'rb')
                    ftp.storbinary(f'STOR {remoteFolderTree[1]}', fp, 1024)
                    previousFilePath = remoteFolderTree[0]
                    numFilesOK = uploadedOK(needupload, numFilesOK)
                    break
                except Exception as e:
                    if retries == 0:
                        log(f'Error on  first attempt uploading {needupload} via FTP: {e}')
                        time.sleep(1)
                    else:
                        log(f'Error on second attempt uploading {needupload} via FTP: {e}')
        log(f'STATUS: {numFilesOK} of {numNewFiles} files uploaded OK')
    try:
        ftp.quit()
    except:
        pass


def commenceDbx(app_key):
    if os.path.isfile(DROPBOX_TOKEN):
        try:
            with open(DROPBOX_TOKEN, 'r') as f:
                refresh_token = f.readline()
        except Exception as e:
            log(f'Exception reading Dropbox token: {e}')
            log('STATUS: No Dropbox token found. Re-auth required')
            return
    else:
        log('STATUS: No Dropbox token found. Re-auth required')
        return
    try:
        with dropbox.Dropbox(oauth2_refresh_token=refresh_token, app_key=app_key) as dbx:
            dbx.users_get_current_account()
    except AuthError as err:
        log(f'Dropbox Auth error: {err}')
        log('STATUS: Invalid Dropbox access token')
        return
    except Exception as e:
        log(f'Exception signing in to Dropbox: {e}')
        log('STATUS: Exception signing in to Dropbox')
        return
    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    numNewFiles = len(newFiles)
    if numNewFiles == 0:
        log('STATUS: No new files to upload')
    else:
        numFilesOK = 0
        for needupload in newFiles:
            log(f'Uploading {needupload}')
            # Format the destination path to strip the /home/pi/photos off:
            shortPath = makeShortPath('', needupload)
            path,filename = os.path.split(shortPath)
            result = dbx_upload(dbx, needupload, path, '', filename)
            if result == None:
                log(f'Error uploading {needupload} via DBX')
            else:
                numFilesOK = uploadedOK(needupload, numFilesOK)
        log(f'STATUS: {numFilesOK} of {numNewFiles} files uploaded OK')


def dbx_upload(dbx, fullname, folder, subfolder, name, overwrite=True):
    """
    Upload a file.
    Return the request response, or None in case of error
    """
    path = (f"/{folder}/{subfolder.replace(os.path.sep, '/')}/{name}")
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
    except ApiError as err:
        if (err.error.is_path() and
            err.error.get_path().reason.is_insufficient_space()):
            log('STATUS: Dropbox upload failed due to insufficient space')
        else:
            log(f'Dropbox API error {err}')
            log(f'Dropbox API errormsg text {err.user_message_text}')
            log('STATUS: Dropbox API error')
        return None
    except Exception as e:
        log(f'Unexpected Dropbox error: {e}')
        log('STATUS: Exception uploading to Dropbox')
        return None
    #log(f'Dropbox uploaded as {res.name.encode('utf8')})
    #log(f'Dropbox result = {res}')
    return res


def reauthDropbox(APP_KEY):
    log('Commencing Dropbox re-auth')
    try:
        auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, use_pkce=True, token_access_type='offline')
        auth_url = auth_flow.start()
        print ('')
        print ('The next step is to tell Dropbox it can trust the intvlm8r.')
        print ('Copy this link to somewhere you can open it in a browser:')
        print (auth_url)
        print ('')
        auth_code = input("Enter the auth code here: ").strip()
        try:
            oauth_result = auth_flow.finish(auth_code)
        except Exception as e:
            log('STATUS: Error in Dropbox re-auth')
            log(f'Error in Dropbox re-auth : {e}')
            return(1)
        with open(DROPBOX_TOKEN, 'w') as f:
            f.write(oauth_result.refresh_token)
        log('Completed Dropbox re-auth')
        print ('')
        print ('Completed Dropbox re-auth OK.')
        response = input("Shall we try uploading some images? [Y/n]: ")
        response = response.lower()
        if response == 'y' or response == '':
            return 0
    except Exception as e:
        print ('')
        print('Error in Dropbox re-auth. (See /home/pi/www/static/piTransfer.log for details)')
        print ('')
        log('STATUS: Error in Dropbox re-auth')
        log(f'Error in Dropbox re-auth : {e}')
    return 1


def commenceSftp(sftpServer, sftpUser, sftpPassword, sftpRemoteFolder):
    # now, connect and use paramiko Transport to negotiate SSH2 across the connection
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #Set the default
        sftpPort=22
        if ':' in sftpServer:
            sftpPort = int(sftpServer.split(':')[1])
            sftpServer = sftpServer.split(':')[0]
            log(f'sftpServer={sftpServer}, port={sftpPort}')
        # get host key, if we know one
        try:
            if sftpServer in open(KNOWN_HOSTS_FILE).read():
                #If the host exists, we'll ONLY accept the current saved key. If it DOESN'T exist, we'll gladly add it to the collection:
                ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
                log(f'Paramiko found {sftpServer} in host keys file & set RejectPolicy')
            ssh.load_host_keys(KNOWN_HOSTS_FILE)
            log('Paramiko loaded host keys file OK')
        except Exception as e:
            log(f'Paramiko unable to open host keys file: {e}')
        ssh.connect(
            hostname=sftpServer,
            port=sftpPort,
            username=sftpUser,
            password=sftpPassword,
        )
        sftp = ssh.open_sftp()
    except paramiko.AuthenticationException as e:
        log(f'Authentication failed: {e}')
        log('STATUS: SFTP Authentication failed')
        return
    except paramiko.SSHException as e:
        log(f'Unable to establish SSH connection: {e}')
        if ('Connection timed out' in str(e)):
            log(f'STATUS: SFTP timed out connecting to {sftpServer}')
        else:
            log('STATUS: SFTP Unable to establish SSH connection')
        return
    except paramiko.BadHostKeyException as e:
        log(f"Unable to verify server's host key: {e}")
        log("STATUS: SFTP Unable to verify server's host key")
        return
    except Exception as e:
        log(f'Exception signing in to SFTP server: {e}')
        log('STATUS: SFTP exception signing in')
        return

    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    numNewFiles = len(newFiles)
    if numNewFiles == 0:
        log('STATUS: No files to upload')
    else:
        numFilesOK = 0
        previousFilePath = ''
        for needupload in newFiles:
            for retries in range(2):
                log(f'Uploading {needupload}')
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
                                except Exception as e:
                                    log(f'Unexpected path/folder error in SFTP: {e}')
                    sftp.put(needupload, remoteFolderTree[1])
                    previousFilePath = remoteFolderTree[0]
                    numFilesOK = uploadedOK(needupload, numFilesOK)
                    break
                except Exception as e:
                    if retries == 0:
                        log(f'Error on  first attempt uploading {needupload} via SFTP: {e}')
                        time.sleep(1)
                    else:
                        log(f'Error on second attempt uploading {needupload} via SFTP: {e}')
        log(f'STATUS: {numFilesOK} of {numNewFiles} files uploaded OK')
    try:
        sftp.close()
    except:
        pass
    try:
        ssh.close()
    except:
        pass


def commenceGoogle(remoteFolder):
    """
    Create a Drive service
    """
    auth_required = True
    #Have we got some credentials already?
    storage = Storage(GOOGLE_CREDENTIALS)
    credentials = storage.get()
    try:
        if credentials:
            # Check for expiry
            if credentials.access_token_expired:
                log ('Google token has expired')
                if credentials.refresh_token is not None:
                    credentials.refresh(httplib2.Http())
                    log ('Google token refreshed OK')
                    auth_required = False
                else:
                    log ('Google refresh_token is None')
            else:
                auth_required = False
        else:
            log ('Google could not find or could not access credentials')
    except:
        # Something went wrong - try manual auth
        log('Google Cached Auth failed')

    if auth_required:
        log('STATUS: Aborted. Google requires re-authentication')
        return 0
    else:
        log('Auth NOT required')
    #Get the drive service
    try:
        http_auth = credentials.authorize(httplib2.Http())
        DRIVE = discovery.build('drive', 'v2', http_auth, cache_discovery=False)
    except Exception as e:
        log(f'Error creating Google DRIVE object: {e}')
        log('STATUS: Error creating Google DRIVE object')
        return 0
    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    numNewFiles = len(newFiles)
    if numNewFiles == 0:
        log('STATUS: No files to upload')
    else:
        numFilesOK = 0
        previousFilePath = ''
        for needupload in newFiles:
            log(f'Uploading {needupload}')
            # Format the destination path to strip the /home/pi/photos off:
            shortPath = makeShortPath(remoteFolder, needupload)
            log(f'ShortPath: {shortPath}')
            remoteFolderTree = os.path.split(shortPath)
            if previousFilePath != remoteFolderTree[0]:
                ImageParentId = None
                # Confirm the tree exists, or build it out:
                foldersList = remoteFolderTree[0].split("/")
                if len(foldersList) != 0:
                    for oneFolder in foldersList:
                        childFolderId = getGoogleFolder(DRIVE, oneFolder, ImageParentId)
                        if childFolderId is None:
                            #Nope, that folder doesn't exist. Create it:
                            newFolderId = createGoogleFolder(DRIVE, oneFolder, ImageParentId)
                            if newFolderId is None:
                                log('Aborted uploading to Google. Error creating newFolder')
                                log(f'STATUS: Google upload aborted. {numFilesOK} of {numNewFiles} files uploaded OK')
                                return 0
                            else:
                                ImageParentId = newFolderId
                        else:
                            ImageParentId = childFolderId
            #By here we have the destination path id
            #Now upload the file
            file_name = remoteFolderTree[1]
            try:
                media = MediaFileUpload(needupload, mimetype='image/jpeg')
                result = DRIVE.files().insert(media_body=media, body={'title':file_name, 'parents':[{u'id': ImageParentId}]}).execute()
                if result is not None:
                    numFilesOK = uploadedOK(needupload, numFilesOK)
                else:
                    log(f"Bad result uploading '{needupload}' to Google: {result}")
            except Exception as e:
                errorMsg = str(e)
                log(f'Error uploading {needupload} via Google: {errorMsg}')
                if 'returned' in errorMsg:
                    errorReason = errorMsg.split('"')[1]
                    log(f'STATUS: Google error: {errorReason}')
                    if 'The user has exceeded their Drive storage quota' in errorReason:
                        log('Google upload aborted - no space')
                        return 0
            previousFilePath = remoteFolderTree[0]
        log(f'STATUS: {numFilesOK} of {numNewFiles} files uploaded OK')
    return 0


def getGoogleFolder(DRIVE, remoteFolder, parent=None):
    """
    Find and return the id of the remote folder
    """
    log(f"Testing if folder '{remoteFolder}' exists.")
    q = []
    q.append("title='{remoteFolder}'")
    if parent is not None:
        q.append("'%s' in parents" % parent.replace("'", "\\'"))
    q.append("mimeType contains 'application/vnd.google-apps.folder'")
    q.append("trashed=false")
    params = {}
    params['q'] = ' and '.join(q)
    files = DRIVE.files().list(**params).execute()
    log(f'FILES returned this: {files}')
    if len(files['items']) == 1:
        remoteFolderId = files['items'][0]['id']
        remoteFolderTitle = files['items'][0]['title']
        log(f"Found the folder '{remoteFolderTitle}'. Its Id is '{remoteFolderId}'")
        return remoteFolderId
    else:
        return None


def createGoogleFolder(DRIVE, newFolder, parentId=None):
    log(f"About to create folder '{newFolder}'.")
    try:
        body = {
          'title': newFolder,
          'mimeType': "application/vnd.google-apps.folder"
        }
        if parentId:
            body['parents'] = [{'id': parentId}]
        newFolderId = DRIVE.files().insert(body = body).execute()
        return newFolderId['id']
    except Exception as e:
        log(f'Error in createGoogleFolder : {e}')


def reauthGoogle():
    log('Commencing Google re-auth')
    if os.path.isfile('client_secrets.json'):
        try:
            storage = Storage(GOOGLE_CREDENTIALS)
            credentials = storage.get()
            if credentials:
                log ('Google re-auth found GOOGLE_CREDENTIALS')
            else:
                log ('Google re-auth did not find GOOGLE_CREDENTIALS')
            flow = client.flow_from_clientsecrets('client_secrets.json',
                scope='https://www.googleapis.com/auth/drive',
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_uri = flow.step1_get_authorize_url()

            print ('')
            print ('The next step is to tell Google it can trust the intvlm8r.')
            print ('Copy this link to somewhere you can open it in a browser:')
            print (auth_uri)
            print ('')
            auth_code = input('Enter the auth code: ')
            credentials = flow.step2_exchange(auth_code)
            storage.put(credentials)
            log('Completed Google re-auth')
            print ('')
            print ('Completed Google re-auth OK.')
            response = input("Shall we try uploading some images? [Y/n]: ")
            response = response.lower()
            if response == 'y' or response == '':
                return 0
        except Exception as e:
            print ('')
            print('Error in Google re-auth. (See /home/pi/www/static/piTransfer.log for details)')
            print ('')
            log('STATUS: Error in Google re-auth')
            log(f'Error in Google re-auth : {e}')
    else:
        print ('')
        print('Error: client_secrets.json file is missing')
        print ('')
        log('STATUS: Google upload failed: client_secrets.json file is missing')
    return 1


def commenceRsync(rsyncUsername, rsyncHost, rsyncRemoteFolder):
    """
    (r)syncs the Pi's photos/ folder with a remote location
    """
    log('Commencing rsync')
    newFiles = list_New_Images(PI_PHOTO_DIR, UPLOADED_PHOTOS_LIST)
    numNewFiles = len(newFiles)
    if numNewFiles == 0:
        log('STATUS: No files to upload')
    else:
        numFilesOK = 0
        localPath  = os.path.join(PI_PHOTO_DIR, 'DCIM')
        try:
            #Upload/dir-sync happens here
            if not rsyncRemoteFolder.startswith('/'):
                rsyncRemoteFolder = '/' + rsyncRemoteFolder
            if not rsyncRemoteFolder.endswith('/'):
                rsyncRemoteFolder += '/'
            destination = rsyncUsername + '@' + rsyncHost + ':' + rsyncRemoteFolder
            cmd = ['/usr/bin/rsync', '-avz', '--rsh=/usr/bin/ssh', localPath, destination]
            result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, encoding='utf-8')
            (stdoutdata, stderrdata) = result.communicate()
            if stdoutdata:
                stdoutdata = stdoutdata.strip()
                #log(f'rsync stdoutdata = {stdoutdata}.')
            if stderrdata:
                stderrdata = stderrdata.strip()
                log(f"rsync err'd with stderrdata = {stderrdata}")
                if 'Host key verification failed' in stderrdata:
                    log('STATUS: rsync host key verification failed')
                elif 'Permission denied' in stderrdata:
                    log('STATUS: rsync error: permission denied')
                else:
                    log('STATUS: rsync error')
            # wait until process is really terminated
            exitcode = result.wait()
            if exitcode == 0:
                log('rsync exited cleanly')
                uploadedList = stdoutdata.splitlines()
                for uploadedFile in uploadedList:
                    uploadedFile = os.path.join(PI_PHOTO_DIR, uploadedFile)
                    if os.path.isfile(uploadedFile):
                        numFilesOK = uploadedOK(uploadedFile, numFilesOK)
                log(f'STATUS: {numFilesOK} files uploaded OK')
            else:
                log('rsync exited with a non-zero exitcode')
                #log('STATUS: rsync error') - I assume this is not needed, as a non-zero error would have populated stderrdata
        except Exception as e:
            log(f'Error uploading via rsync: {e}')
            log('STATUS: rsync error')
    return


def uploadedOK(filename, filecount):
    """
    The file has been uploaded OK. Add it to the UPLOADED_PHOTOS_LIST.
    Delete local file, thumb, preview & metadata if required
    """
    log(f' Uploaded {filename}')
    if deleteAfterTransfer:
        try:
            os.remove(filename)
            log(f'  Deleted {filename}')
            deleteThumbsInfo(filename)
            for folder,suffix in [(PI_THUMBS_DIR, '-thumb.JPG'), (PI_PREVIEW_DIR, '-preview.JPG')]:
                try:
                    file2Delete = filename.replace( PI_PHOTO_DIR, folder)
                    file2Delete = os.path.splitext(file2Delete)[0] + suffix
                    if os.path.isfile(file2Delete):
                        os.remove(file2Delete)
                        log(f'  Deleted {file2Delete}')
                except Exception as e:
                    log(f'Error deleting file {file2Delete} : {e}')
        except Exception as e:
            log(f'Unknown error in uploadedOK: {e}')
    else:
        with open(UPLOADED_PHOTOS_LIST, "a") as historyFile:
            historyFile.write(filename + "\n")
    return (filecount + 1)


# TY SO: https://stackoverflow.com/questions/4710067/using-python-for-deleting-a-specific-line-in-a-file
def deleteThumbsInfo(filepath):
    """
    Delete this file's metadata from PI_THUMBS_INFO_FILE
    """
    try:
        filename = filepath.rsplit('/',1)[1]
        with open(PI_THUMBS_INFO_FILE, "r") as f:
            lines = f.readlines()
        with open(PI_THUMBS_INFO_FILE, "w") as f:
            for line in lines:
                if filename not in line.strip("\n"):
                    f.write(line)
    except Exception as e:
        log(f'Exception deleting {filename} from  {PI_THUMBS_INFO_FILE}')
        log(f'Exception: {e}')
    return


def log(message):
    try:
        logging.info(message)
    except Exception as e:
        print(f'error: {e}')
        #pass


if __name__ == '__main__':
    main(sys.argv[1:])
