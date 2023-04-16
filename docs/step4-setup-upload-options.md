# Setup upload options

The intvlm8r provides five methods to automatically upload images off the Raspberry Pi. FTP is baked into the Pi by default, however the others require you to install extra software components.

The setup steps on this page require you to have already installed the required components. See [step1-setup-the-Pi.md, step 33](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md#heres-where-all-the-software-modules-are-installed-this-might-take-a-while)

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

NB: This process was last confirmed accurate in March 2023.

1. Before you can use Dropbox, you need to have installed the Dropbox API at the setup stage. If you're not sure, browse to the /transfer page and open the "Upload method" pulldown. If Dropbox is greyed out and can't be selected, that option has not been installed. To install it, jump to step 32 of the [step1-setup-the-Pi.md](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md) process.

2. Browse to [https://www.dropbox.com/developers](https://www.dropbox.com/developers)
3. Click the "App console" button in the top right-hand corner:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750027-10aca180-d55b-11e9-8945-cb62cceb24e7.jpg" width="80%">
 </p>

4. Sign in to your account.
5. Click "Create App":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750062-24f09e80-d55b-11e9-95f3-cba0c8ed7ead.jpg" width="80%">
 </p>

6. Choose the radio buttons for "Scoped access", "App Folder", give it a name and then click Create App:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093266-0226a41b-0313-423b-a289-8d7fb0819a45.png" width="80%">
 </p>

7. Change the "App folder name" if required, and then copy the "App key":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093329-9f4f4676-5c85-4cde-b9da-30bdd5d8f67b.png" width="80%">
 </p>

8. Switch to the Permissions tab, click to check "files.content.write" and then Submit.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178094082-6951b16c-7e33-4dc6-a959-1b562f0101c5.png" width="80%">
 </p>
 
9. If you're using Windows 10 and signed into that Dropbox account, you should soon receive a popup to let you know the app has been created, and see that it now appears in your Dropbox folders list:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093395-73d26b10-ce7a-4227-9a8a-909bdaf8ba48.png" width="40%">
</p>
<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093417-00b1b271-2094-4c90-a3de-4ea1a20f24af.png" width="25%">
 </p>

10. Now login to the intvlm8r, choose Dropbox for the Transfer Method on the /Transfer page, paste the App key from Step 6 into this field and click Apply.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093485-10bf1e6b-e2b7-4dd5-ab3b-f7c661eaf114.png" width="40%">
</p>

11. Navigate to the www folder:
```text
cd ~/www
```

12. The final stage is to authorise the intvlm8r to access your Dropbox account. SSH to the intvlm8r and run the piTransfer script with the 'reauthDropbox' switch:
```text
python3 piTransfer.py reauthDropbox
``` 

13. It will prompt you to copy a long link to your browser:
```text
The next step is to tell Dropbox it can trust the intvlm8r.
Copy this link to somewhere you can open it in a browser:
https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=12345678abcd&token_access_type=offline&code_challenge=12345678abcd12345678abcd12345678abcd&code_challenge_method=S256
```

14. Copy the link to your PC and browse to it. You'll be prompted to sign-in if you're not already.

15. At the "Before you connect this app..." prompt, click Continue:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093648-ea449cf2-0669-48f6-a99d-8497586d42eb.png" width="60%">
</p>

16. At the "<Your app name from Step 5> would like to:" prompt, click Allow:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093706-9b3c1f6a-bbab-47a8-8bc6-1e24218f31a7.png" width="60%">
</p>

17. When the "Access Code [is] Generated", copy this to the clipboard:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/178093759-dfd897ad-2306-475f-859f-a633a62d2d13.png" width="60%">
</p>

18. Finally, return to the intvlm8r and paste the new code into the awaiting prompt:

```text
The next step is to tell Dropbox it can trust the intvlm8r.
Copy this link to somewhere you can open it in a browser:
https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=12345678abcd&token_access_type=offline&code_challenge=12345678abcd12345678abcd12345678abcd&code_challenge_method=S256

Enter the auth code here: abcd12345678ZZZZZZZZZZZZZabcd12345678ZZZZZZZZZZZZZ
```

19. If this succeeds, you'll be prompted to take it for a test-run:

```text
Completed Dropbox re-auth OK.
Shall we try uploading some images? [Y/n]: 
```
20. If you press Return or Y, the piTransfer script will attempt an upload. Pressing any other option will abort at this stage.

21. Hopefully it's all working OK. If the images don't materialise in your Dropbox, check out the transfer error log at ```/home/pi/www/static/piTransfer.log```.


<br>

[Top](#setup-upload-options)
<hr />

## Google Drive

Google has discontinued the integration the intvlm8r previously used to upload images to Google Drive. [[Reference](https://developers.googleblog.com/2022/02/making-oauth-flows-safer.html)]

This option was removed from the code in release 4.5.2, although I'm still hoping to find an alternative integration for 'headless' devices like the Raspberry Pi.

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
