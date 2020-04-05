# Setup upload options

The intvlm8r provides four methods to automatically upload images off the Raspberry Pi:
- FTP
- SFTP
- Dropbox
- Google Drive

<br/>
<hr />
## FTP & SFTP

There's no special config required to upload to an (S)FTP site. All you need to do is create an account on the server and paste those credentials into the /transfer page.

> Be aware that the upload credentials are saved as plain text - unencrypted - in the invtlm8r's .ini file.

<hr />
## Dropbox

Prior to using Dropbox you need to perform some authentication steps to allow the intvlm8r to upload photos into your Dropbox account.

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

NB: This process was last confirmed accurate on September 12th, 2019.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/64750110-46ea2100-d55b-11e9-89e4-6ffe30ce95cc.jpg" width="40%">
</p>

<hr />
## Google Drive

1. Before you can use Google Drive, you need to have installed the Google API at the setup stage. If you're not sure, browse to the /transfer page and open the "Upload method" pulldown. If Google Drive is greyed out and can't be selected, the options weren't installed. To install them, jump to step 32 of the [step1-setup-the-Pi.md](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md) process.

2. Google Drive won't let an app like the intvlm8r upload files without you first granting consent. Navigate to console.developers.google.com/start/api?id=drive and login to your Google account to commence this process:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/78420245-14d81200-7699-11ea-85fa-f0c404b95d18.png" width="60%">
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



6. Click 'Go to credentials' to move to the next step.


<p align="center">
<img src="" width="80%">
 </p>



. SSH to the Raspberry Pi & login.

. Navigate to the www folder:
```text
cd 
```

. Run the piTransfer script with the 'reauthGoogle' switch:
```text
python3 piTransfer.py reauthGoogle
```

. It will prompt you to copy a long link to your browser:
```text
Go to this link in your browser:
https://accounts.google.com/o/oauth2/auth?client_id=712345678903-fpasdfghjklpoiuytrewqajet9g8hgkj.apps.googleusercontent.com&redirect_uri=urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&access_type=offline&response_type=code
```

8. When you open that link in a browser, 


References:
- [Google Drive API - Python Quickstart](https://developers.google.com/drive/api/v3/quickstart/python)
- [Using the G Suite APIs](https://codelabs.developers.google.com/codelabs/gsuite-apis-intro/#0)

<br>

## Next steps are:
- [PCB Assembly](/docs/step5-pcb-assembly.md)
<br>
<hr >
