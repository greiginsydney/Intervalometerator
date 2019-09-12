# Setup upload options

The intvlm8r provides 3 methods to upload images off the system:
- FTP
- SFTP
- Dropbox

<br/>

## FTP & SFTP

There's no special config required to upload to an (S)FTP site. All you need to do is create an account on the server and paste those credentials into the /transfer page.

> Be aware that the upload credentials are saved as plain text - unencrypted - in the invtlm8r's .ini file.

## Dropbox

Prior to using Dropbox you need to perform some authentication steps to allow the intvlm8r to upload photos into your Dropbox account.

1. Browse to [https://www.dropbox.com/developers](https://www.dropbox.com/developers)
2. Click the "App console" button in the top right-hand corner:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750027-10aca180-d55b-11e9-8945-cb62cceb24e7.jpg" width="80%" style="border:1px solid black">
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

NB: This process was last confirmed accurate on September 12th, 2019.

<br>

## Next steps are:
- [PCB Assembly](/docs/step5-pcb-assembly.md)
<br>
<hr >
