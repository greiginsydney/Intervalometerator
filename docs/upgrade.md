
# Upgrading your Intvlm8r

## Arduino

The upgrade process is the same as you undertook to build it. You need physical access to the Arduino to connect to the programming header, so it can’t be performed remotely. Refer to the walk-through in [step6-program-the-Arduino.md](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step6-program-the-Arduino.md).

## Raspberry Pi

### Which Python are you?

Python 2 was discontinued at the end of 2019, and the intvlm8r code was updated to Python 3 in January 2020.

If your intvlm8r was built prior to the start of 2020 it will be running Python 2. If you're not overly familiar with Linux and the Raspberry Pi & don't feel comfortable performing an in-place upgrade, a full rebuild is recommended.

Peeking into the crontable will reveal which version of Python is being called for the various scheduled tasks. In this example, the intvlm8r is using Python 3:

```text
crontab -e

0 * * * * /usr/bin/python3 /home/pi/www/cameraTransfer.py 2>&1 | logger -t cameraTransfer
0 * * * * /usr/bin/python3 /home/pi/www/piTransfer.py 2>&1 | logger -t piTransfer
```

### Upgrading the Pi

The process to upgrade the Raspberry Pi is no different to the steps you took to originally build the Pi.

In an upgrade scenario the setup script will not overwrite any sensitive files like the Wi-Fi setup in hostapd.conf, and it won’t delete any of the images. It doesn’t touch any of the supporting files that have been created along the way, like intvlm8r.ini, uploadedOK.txt or any of the credentials files used for the Google Drive transfer process.

When from Step 30 you download the repo, the files are all dropped in your user's /home/ folder, and then the setup script moves them to their correct locations, overwriting any existing files in the process.

> Should you have customised any of the HTML, CSS or script files, they will be lost, so please take a backup first. 

The setup 'start' step (Step 32) renames the existing `intvlm8r.py` file to `intvlm8r.old` and renames the `intvlm8r.py.new` file from the repo to become `intvlm8r.py`.

During the setup.sh 'web' step (Step 35) the script checks for the presence of `intvlm8r.old`. If this file is found (indicating this is an upgrade) it will extract its Secret Key and web logins, copying them into the fresh `intvlm8r.py` file just downloaded from GitHub.

The setup script also edits a number of config files on the Pi, but it's been coded to only write the new value if it's not there already.

One file that WILL always be copied across is `/etc/nginx/sites-available/intvlm8r`, however any existing file will be renamed `/etc/nginx/sites-available/intvlm8r.old` first. If you've customised this by adding an SSL certificate or any other tweaks to the web config, please review and reinstate the relevant bits after the script completes.

If the invtlm8r fails after the upgrade completes, review any errors that might have been output to the screen, or the error file at `/home/pi/www/gunicorn.error`.

Start the upgrade process from Step 21 in [step1-setup-the-Pi.md](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md#remote-config-via-ssh).

<br />
