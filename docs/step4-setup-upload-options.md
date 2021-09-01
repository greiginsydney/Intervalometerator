# Setup upload options

The intvlm8r provides four methods to automatically upload images off the Raspberry Pi:
- [FTP](#ftp--sftp)
- [SFTP](#ftp--sftp)
- [Dropbox](#dropbox)
- [Google Drive](#google-drive)
- [rsync](#rsync)

<br/>
<hr />

## FTP & SFTP

There's no special config required to upload to an (S)FTP site. All you need to do is create an account on the server and paste those credentials into the /transfer page.

> Be aware that the upload credentials are saved as plain text - unencrypted - in the invtlm8r's .ini file.

<br>

[Top](#setup-upload-options)
<hr />

## Dropbox

Prior to using Dropbox you need to perform some authentication steps to allow the intvlm8r to upload photos into your Dropbox account.

NB: This process was last confirmed accurate on September 12th, 2019.

1. Browse to [https://www.dropbox.com/developers](https://www.dropbox.com/developers)
2. Click the "App console" button in the top right-hand corner:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750027-10aca180-d55b-11e9-8945-cb62cceb24e7.jpg" width="80%">
 </p>

3. Sign in to your account.
4. Click "Create App":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750062-24f09e80-d55b-11e9-95f3-cba0c8ed7ead.jpg" width="80%">
 </p>

5. Choose the radio buttons for "Dropbox API", "App Folder", give it a name and then click Create App:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750082-3174f700-d55b-11e9-98aa-fcb0a58dca5c.jpg" width="80%">
 </p>

6. Under "OAuth 2", click "Generate":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750093-39349b80-d55b-11e9-96be-70bbda39375e.jpg" width="80%">
 </p>

7. Copy the token that this generates:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750099-3fc31300-d55b-11e9-97ce-ac36105b3165.jpg" width="80%">
 </p>

8. If you're using Windows 10 and signed into that Dropbox account, you should get a popup to let you know the app has been created, and see that it now appears in your Dropbox folders list:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750110-46ea2100-d55b-11e9-89e4-6ffe30ce95cc.jpg" width="40%">
</p>
<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750119-4d789880-d55b-11e9-9909-a20f83eab524.jpg" width="25%">
 </p>

9. You're done. Now login to the intvlm8r, choose Dropbox for the Transfer Method on the /Transfer page, paste the token into this field and click Apply.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750110-46ea2100-d55b-11e9-89e4-6ffe30ce95cc.jpg" width="40%">
</p>

<br>

[Top](#setup-upload-options)
<hr />

## Google Drive

NB: This process was last confirmed accurate on November 9th, 2020.

1. Before you can use Google Drive, you need to have installed the Google API at the setup stage. If you're not sure, browse to the /transfer page and open the "Upload method" pulldown. If Google Drive is greyed out and can't be selected, that option has not been installed. To install it, jump to step 32 of the [step1-setup-the-Pi.md](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md) process.

2. Google Drive won't let an app like the intvlm8r upload files without you first granting consent. Navigate to [https://console.developers.google.com/start/api?id=drive](https://console.developers.google.com/start/api?id=drive) and login to your Google account to commence this process:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78420245-14d81200-7699-11ea-85fa-f0c404b95d18.png" width="50%">
</p>

3. If you don't have any projects yet, you'll see this screen to accept the Google APIs Terms of Service:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78420257-2c16ff80-7699-11ea-83bb-e917e0c6aade.png" width="60%">
</p>

Once you accept the terms and click "Agree and continue" a new project named "My Project" will be created, and the Drive API automatically enabled. Jump to step 5.

4. If instead, your account already has an API project, you'll see this screen:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78419911-210ea000-7696-11ea-8f40-d19145977587.png" width="60%">
</p>

Leave the dropdown showing "Create a project" and click Continue.

5. You'll know the Drive API has been enabled with this confirmation:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78419879-c7a67100-7695-11ea-94a1-70039b5012d3.png" width="60%">
 </p>

Click 'Go to credentials' to move to the next step.

7. Select the highlighted options and then click "What credentials do I need?"

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78466992-6214bc00-774b-11ea-9e02-5c26ba3aa565.png" width="60%">
</p>

8. Click "Set Up Consent Screen":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467008-ac963880-774b-11ea-8513-db358725beee.png" width="50%">
</p>

9. Select "External" and click Create:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467029-d8192300-774b-11ea-83d6-0b8ce9eb6c23.png" width="60%">
</p>

10. The "Step 1 OAuth consent screen" will show. Give your application a name, provide two e-mail addresses at the prompts & then click "SAVE AND CONTINUE":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/98530534-276f9500-22d3-11eb-8ce9-b65e12637889.png" width="80%">
</p>


11. The "Step 2 Scopes" screen will show. Click "ADD OR REMOVE SCOPES":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/98530679-5e45ab00-22d3-11eb-9ac4-bb106cc5eb82.png" width="80%">
</p>

12. Check the box next to Google Drive API as shown (the ../auth/__drive__ scope), then scroll to the bottom and click "UPDATE":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/98530759-75849880-22d3-11eb-9661-384dddcdc71d.png" width="60%">
</p>


13. **Disregard** the popup saying verification is required. Click "CONTINUE":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/98530955-bda3bb00-22d3-11eb-99c2-9e186558be81.png" width="60%">
</p>


14. Click "Credentials" in the menu on the left, and then "+ Create Credentials":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467149-f6335300-774c-11ea-9954-3a18343dc74a.png" width="60%">
</p>

15. From the pop-up, click to select "OAuth client ID":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467187-414d6600-774d-11ea-8b0f-ebcb2d8fb488.png" width="50%">
</p>

16. Choose the Application type of "TVs and Limited Input devices", give your application a name, and then click Create:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/98531103-f6439480-22d3-11eb-83bb-561269a6497d.png" width="80%">
</p>

17. All going well, your new OAuth client and secret have been created. Click OK to acknowledge it:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467209-95f0e100-774d-11ea-95bf-8ea339499216.png" width="50%">
</p>

18. Now on the Credentials page, click the arrow icon shown to download the OAuth client ID as a .json file:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467235-d6e8f580-774d-11ea-8fb5-93a084c5d962.png" width="80%">
</p>

19. The file will be called something like "client_secret_<gibberish>.apps.googleusercontent.com.json". Rename it to client_secrets.json.

20. Copy the file to the Raspberry Pi. It needs to go in the '/home/pi/www' folder.

21. SSH to the Raspberry Pi & login.

22. Navigate to the www folder:
```text
cd /home/pi/www
```

23. Run the piTransfer script with the 'reauthGoogle' switch:
```text
python3 piTransfer.py reauthGoogle
```

24. It will prompt you to copy a long link to your browser:
```text
The next step is to tell Google it can trust the intvlm8r.
Copy this link to somewhere you can open it in a browser:
        
https://accounts.google.com/o/oauth2/auth?client_id=712345678903-fpas1234567g8hgkjpoiuytrewqajet9.apps.googleusercontent.com&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&access_type=offline&response_type=code
```

25. Copy the link to your PC and browse to it. You'll be prompted to sign-in if you're not already.

26. Click to choose an account:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467635-f97d0d80-7751-11ea-80f3-951231212400.png" width="50%">
</p>

27. On the "This app isn't verified" page, click Advanced:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467662-32b57d80-7752-11ea-9109-a78a80a8a5ef.png" width="60%">
</p>

> Your browser might provide a different way of getting to an untrusted URL. This sample screen is from Chromium/Chrome.

28. Click "Go to intvlm8r (unsafe)":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467667-452fb700-7752-11ea-8e77-6b9b0acbb8a9.png" width="60%">
</p>

29. Click "Allow" to grant the intvlm8r access to your Google Drive:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467682-74debf00-7752-11ea-8f76-260824dcc0c8.png" width="50%">
</p>

30. Yes, you're sure. Cick "Allow" again:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467691-86c06200-7752-11ea-840f-693fb7b24689.png" width="50%">
</p>

31. Now click the highlighted icon to copy the code to your clipboard:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78467733-e7e83580-7752-11ea-848b-e8d232124ab7.png" width="50%">
</p>

32. Switch back to the Raspberry Pi. It should be prompting you to enter that code, so paste it in and press return:

```text
The next step is to tell Google it can trust the intvlm8r.
Copy this link to somewhere you can open it in a browser:
https://accounts.google.com/o/oauth2/auth?client_id=712345678903-fpas1234567g8hgkjpoiuytrewqajet9.apps.googleusercontent.com&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&access_type=offline&response_type=code
Enter the auth code: 4/yQasdfghjklg8hgkjewazxcvbnmg8hgkjyhgtrfdewsaqGEw4uWIc
```

33. If this succeeds, you'll be prompted to take it for a test-run (assuming Google Drive was already selected on the /transfer page of course!)

```text
Completed Google re-auth OK.
Shall we try uploading some images? [Y/n]:
```
34. If you press Return or Y, the piTransfer script will attempt an upload. Pressing any other option will abort at this stage.

35. If you _haven't_ already selected Google on the /transfer page, do that now, select the folder into which the images will go, and then return to the Pi.

36. To initate a test transfer - which you can do at any time - run this command:

```text
cd /home/pi/www
python3 piTransfer.py copyNow
```

37. Hopefully it's all working OK. If the images don't materialise in your Google Drive, check out the transfer error log at ```/home/pi/www/static/piTransfer.log```.

<br>

References:
- [Google Drive API - Python Quickstart](https://developers.google.com/drive/api/v3/quickstart/python)
- [Using the G Suite APIs](https://codelabs.developers.google.com/codelabs/gsuite-apis-intro/#0)

<br>
 
[Top](#setup-upload-options)
<hr />

## rsync
 
[rsync](https://en.wikipedia.org/wiki/Rsync) is a Linux utility that lets you synchronise folders between two systems. Once you have rsync setup, the intvlm8r starts a session to your rsync host and the images and folders all synchronise. The sync takes place over ssh so it's secure, and it's compressed, minimising network use.
 
At the completion of a successful rsync 'sync', the remote host provides a list of the files that were synchronised. The count of files is reported to the intvlm8r's status line, and if you have [DeleteAfterTransfer](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/FAQ.md#my-camera-andor-pi-are-running-low-on-storage-how-can-i-delete-old-images) enabled, the local files are deleted.

To setup rsync over ssh you first need to create a local rsa key pair and copy them to the remote host:
 
1. SSH to the Raspberry Pi & login.
 
2. `ssh-keygen` and just hit ENTER in response to all the questions.

The output will look something like this:

 ```bash
pi@BlackPCB:~ $ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/pi/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/pi/.ssh/id_rsa.
Your public key has been saved in /home/pi/.ssh/id_rsa.pub.
The key fingerprint is:
SHA256:lKFoMgmO8EabcdEF123456789+c pi@BlackPCB
The key's randomart image is:
+---[RSA 2048]----+
|oo+o+*..=o++     |
|+=o=+ooOOoo .    |
|o.B.*.o.=+.o     |
| . =oo.oo .      |
|    oO0oS.       |
|   +.oo.+        |
|     OooO        |
|                 |
|                 |
+----[SHA256]-----+
pi@BlackPCB:~ 
```
 
3. As you can see in the above, the key has been saved in /home/pi/.ssh/ as id_rsa. This command will copy it to the remote server:

```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub rsyncuser@10.10.10.10 -f
```
 
(Don't forget to change the username from 'rsyncuser' and the IP address to those of your rsync login and host.)
 
4. Answer "yes" to the prompt, then provide the rsync user's password to authorise the transfer:

```bash
pi@BlackPCB:~ $ ssh-copy-id -i ~/.ssh/id_rsa.pub rsyncuser@10.10.10.10
/usr/bin/ssh-copy-id: INFO: Source of key(s) to be installed: "/home/pi/.ssh/id_rsa.pub"
The authenticity of host '10.10.10.10 (10.10.10.10)' can't be established.
ECDSA key fingerprint is SHA256:lKFoMgmO8EabcdEF123456789+c.
Are you sure you want to continue connecting (yes/no)? yes
rsyncuser@10.10.10.10's password:

Number of key(s) added: 1

Now try logging into the machine, with:   "ssh 'rsyncuser@10.10.10.10'"
and check to make sure that only the key(s) you wanted were added.
```

5. You're done! Now enter some details on the /transfer page and you should be good to go.
 
<br>
 
[Top](#setup-upload-options)
<hr >

## Next steps are:
- [PCB Assembly](/docs/step5-pcb-assembly.md)
<br>
<hr >
