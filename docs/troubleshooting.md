# Troubleshooting

Jump to the relevant section:

- [Browser Errors](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#browser-errors)
- [Application Errors](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#application-errors)
- [Camera Errors](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#camera-errors)
- [USB Errors](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#usb-errors)
- [Transfer Errors](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#transfer-errors)


<hr/>

## Browser Errors

A browser error will show when the Pi is unable to present a web-page. 

### "Refused to Connect"

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/92381622-8fc4bd80-f14e-11ea-8974-568a533716e6.png" width="50%">
</p>

Assuming you have network connectivity to the intvlm8r, the first suspect here is 'nginx'.

Debug with `sudo systemctl status nginx`, and review the log at `/var/log/nginx/error.log`.
 
 (`/home/pi/www/gunicorn.error` probably won't tell you anything, as your request for a web-page isn't making it that far.)


### 500 - Internal Server Error

There's something wrong, most likely in intvlm8r.py.

SSH or SCP to the Pi and check out the error log at `/home/pi/www/gunicorn.error`.

### 502 - Bad Gateway

In a working (established) system, this indicates the Pi is too busy to present a web-page. You're most likely to encounter this for the first minute or two after the Pi starts, as it's copying images from the camera. It's also commonplace to receive this if you clicked "Transfer Now" from the Transfer Settings page and there were a lot of images to copy across. Wait a little while and refresh the page in your browser.

If you're seeing this as a result of a build step, or you're working on the code, it's usually a bug. SSH or SCP to the Pi and check out the error log at `/home/pi/www/gunicorn.error`. Scroll to the bottom and it will usually identify the offending line number and issue that's stopping it presenting the page.

### 504 - Gateway Time-out

The Pi's probably still booting. Wait a little while and refresh the page in your browser.

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#troubleshooting)
<hr/>

## Application Errors 

Application Errors are usually the messages that display in a red banner in the intvlm8r's web-page.

Other application errors are those values that show as "Unknown" on various pages, or if a change isn't reflected in the re-drawn page.

### Unknown Model / No or unknown camera detected
There are many reasons why the app might report "Unknown Model", or "No or unknown camera detected".

If you receive this error after having attempted to wake the camera, the first thing to check is if the camera is indeed awake, as the process has two steps: wake the camera via the remote cable, then talk to it using gphoto2 over USB.

- #### If it's not awake
    This indicates there's an issue with the remote control interfacing.
    - First off though, is the camera's power OK?? Make sure you can wake it by half-pressing the shutter button. If not, check the 7.5V regulator and related cabling/connectors.
    - Are the J3 and J4 jumpers set correctly, and not fallen off?
    - Are the connectors at both ends of the remote control cable seated firmly?
- #### If it's awake
    Something's awry with the USB.
    - The camera might be connected to the wrong USB port on a Pi Zero. (Check the component overlay in the [docs](https://github.com/greiginsydney/Intervalometerator/tree/master/docs) folder.)
    - It's an unknown camera (not compatible with the intvlm8r).
    - It's worth checking it's not an issue with the intvlm8r's code. For this you can ssh to the Pi and run some of the python gphoto scripts that are installed by default. Try this:
    ```python
    cd /usr/local/share/python-gphoto2/examples
    sudo python3 camera-summary.py 
    ```
     If this responds with information about your camera, there's an issue in the intvlm8r, so focus your debugging on `/home/pi/www/intvlm8r.py`. If it fails, there's a deeper underlying USB issue. See [USB errors](https://github.com/greiginsydney/Intervalometerator/wiki/Troubleshooting#usb-errors) below.

### "Unknown"
Inside the python code, each call to a web-page starts with the variables initialised as "Unknown", and they're progressively updated with their intended value as the Pi, Arduino or camera are queried in the process of preparing the page.

A value that remains "Unknown" when the page is served to the user has failed the above step. The most common instances of Unknown will be the result of a failure in the I2C communication with the Arduino, but these will usually only be a transient failure, and a refresh of the web-page will usually result in all expected values being returned.

If _all_ values from the Arduino report Unknown continuously, check:
- The aerial I2C lines between the Pi and Arduino are connected, and they're the right way around. (Refer the images on the [PCB assembly](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step4-pcb-assembly.md) page.)
- The Arduino isn't asleep. (You might encounter this when bench testing, where you have the Pi powered using the link combo's as described in the [wiki/Advanced Config](https://github.com/greiginsydney/Intervalometerator/wiki/Advanced-Config), and the Arduino thinks the Pi is off, so it's gone to sleep too.) To check for this, link the MC pins. If the LED doesn't light, it means the Pi is asleep. Briefly short the Reed pins to wake it - but beware that it might instantly go back to sleep if you have the J2 jumpers in an off-normal state.
- Check the config of the Pi to make sure it's not trying to talk too fast to the Arduino. Check step 100 in [step1-setup-the-Pi.md](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step1-setup-the-Pi.md#continue-with-the-piarduino-interfacing)
- You haven't accidentally (or otherwise) used the 5V version of the Arduino Pro Mini have you?

### Could not claim the USB device
Another thread (or user) is currently accessing the camera. This may just be a background process copying images from the camera to the Pi. This will normally be a transient error.

### No storage info available
This message displays if the camera reports a missing or faulty memory card. 

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#troubleshooting)
<hr/>

## Camera Errors

### Dead memory card - 0 images on camera

This screen-grab of the intvlm8r helped us diagnose a dead memory card.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/57963739-58843900-796c-11e9-90ac-8e69e1531ec0.png" width="50%">
</p>

The System Date and Next/Last Shots all report that the intvlm8r is attempting to fire off photos. That we can see the camera is a 600D means (1) it's connected, (2) it's awake, and (3) that the USB port is working between it and the Pi.

Had the camera reported it had 'nn' images and a datestamp for the last one we would have suspected the remote control cable had become dislodged, but the lack of this info suggested otherwise.

Manual intervention at this stage was required, and an in-person check of the camera reported it saying "No card in camera". A test for this issue was added to intvlm8r.py, and it now reports "No storage info available" to the web-page.

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#troubleshooting)
<hr/>

## USB Errors
If there are problems with USB communication between the Pi and the camera lots of things will stop working, but the Intervalometerator's designed so that the camera is still able to take photos if the Pi or USB go faulty.

USB errors will usually manifest themselves as the total failure to communicate with the camera, beyond being able to wake it and fire scheduled photos. The browser will report "Unknown Model" and/or "No or unknown camera detected".

### Test steps
Before proceeding here, confirm first this isn't a different problem. See the test steps in [Unknown Model / No or unknown camera detected](https://github.com/greiginsydney/Intervalometerator/wiki/Troubleshooting#unknown-model--no-or-unknown-camera-detected) earlier on this page.
Assuming the web-site's responding we know the Pi's running, which confirms it's powered and that it's "sane" - the OS, file system and application all appear to be sufficiently intact.
There are two paths to take now: hardware (wiring) and software. The latter is the quicker and easier to test - and less intrusive too:
#### Software 

SSH to the Pi, login and issue the command `lsusb`. All going well, something like this should be the output - with the obvious clue here being your camera is reported:
```
pi@intvlm8r-zero:~ $ lsusb
Bus 001 Device 002: ID 04a9:3215 Canon, Inc.
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

The absence of the camera can still be either hardware or software, so let's continue. Here's an example of a Pi in a faulted state:

```linux
pi@intvlm8r-zero:~ $ lsusb
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

"dmesg" might reveal issues with USB. (`man dmesg`:"dmesg is used to examine or control the kernel ring buffer".)
```
pi@intvlm8r-zero:~ $ dmesg | grep usb
[581537.438430] usb 1-1: new high-speed USB device number 104 using dwc_otg
[581537.799353] usb 1-1: New USB device found, idVendor=04a9, idProduct=3215
[581537.799375] usb 1-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
[581537.799387] usb 1-1: Product: Canon Digital Camera
[581537.799413] usb 1-1: Manufacturer: Canon Inc.
[585135.207038] usb 1-1: USB disconnect, device number 104
[585137.496790] usb 1-1: new high-speed USB device number 105 using dwc_otg
[585137.738684] usb 1-1: New USB device found, idVendor=04a9, idProduct=3215
[585137.738721] usb 1-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
[585137.738731] usb 1-1: Product: Canon Digital Camera
[585137.738738] usb 1-1: Manufacturer: Canon Inc.
[588735.289881] usb 1-1: USB disconnect, device number 105
[588737.469583] usb 1-1: new high-speed USB device number 106 using dwc_otg
[588737.711450] usb 1-1: New USB device found, idVendor=04a9, idProduct=3215
[588737.711492] usb 1-1: New USB device strings: Mfr=1, Product=2, SerialNumber=0
[588737.711503] usb 1-1: Product: Canon Digital Camera
[588737.711511] usb 1-1: Manufacturer: Canon Inc.
[592334.790059] usb usb1-port1: disabled by hub (EMI?), re-enabling...
[592334.790093] usb 1-1: USB disconnect, device number 106
[592335.199838] usb 1-1: new high-speed USB device number 107 using dwc_otg
[592335.479824] usb 1-1: device descriptor read/64, error -71
[592335.809886] usb 1-1: device descriptor read/64, error -71
```
The fix in this case was a reboot of the Pi, as simple as `sudo reboot now`. The faulty Pi in this real-world extract was running on the bench in "Always On" mode. It's less likely you'll encounter this problem in the field if the Pi is only running for a set period per day then shutting down.

If there are no obvious errors in the dmesg output, a reboot of the Pi might be in order anyway. If camera comm's is still down after a reboot, continue to Hardware:

#### Hardware

Still crook?
- Try re-seating the USB connectors at both ends. Be careful with the micro USB connector on the Pi Zero as these are relatively fragile.
- Is the USB cable OK? Check carefully to ensure it's not been accidentally damaged by being pinched in the box's seal when it was closed.
- Are you using the correct USB port on the Pi Zero? It's labelled on the white PCB overlay, but you need to be using the USB socket closest to the HDMI socket. The other USB socket is only a power input - it's useless for communicating over.
- Is there any sign of physical damage to the USB socket? It's not sitting at an angle: left or right, pointing up or down? It's only a surface-mounting socket, so it could have been damaged if the cable was pulled or bumped.
- If you happen to have another *supported* camera handy, move the USB connector to it, wake it, then see if everything comes good. If it does, the problem is with the original camera. 
- If you have a keyboard or mouse handy, plug it into the USB socket. If the socket and board are good, the device should show signs of life. Tap the CapsLock, NumLock and ScrollLock buttons and see if the corresponding LED lights, or that the LED on your optical mouse is illuminated.
- If the keyboard/mouse test fail, it's starting to look like you have a damaged Pi or cabling. Replace the OTG cable (if you're using one to convert to USB-A) if you haven't already. 
- If you've reached this step it's not looking good. Try a power-down reboot of the Pi (rather than just a software reboot). To _elegantly_ do this, remove the jumper that's on the top two pins of J2. Once the Pi has shutdown, remove power from the board, reinstate the top J2 jumper and reapply power.
- If USB is still down, replace the Pi and/or entire PCB.

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#troubleshooting)
<hr/>

## Transfer Errors 

"Transfer errors" are those that result in images not being transferred from the camera to the Pi, or from the Pi to your "off-Pi" destination (i.e. FTP, SFTP, Dropbox).

### Check the cron jobs

Whilst an ad-hoc transfer from camera to Pi can be initiated by the "Copy Now" button on the Transfers page, all other transfers take place as a result of a "cron job" - a scheduled task.

`crontab -e` will confirm the tasks have been set. The first time you issue this command it will prompt for your preferred editor. If you're unsure, choose nano, option 1:

```text
crontab -e

Select an editor.  To change later, run 'select-editor'.
  1. /bin/nano        <---- easiest
  2. /usr/bin/vim.tiny
  3. /bin/ed

Choose 1-3 [1]:
```

... and then the "cron tab", the cron table file opens:

```text
0 * * * * /usr/bin/python3 /home/pi/www/cameraTransfer.py
0 * * * * /usr/bin/python3 /home/pi/www/piTransfer.py
```

The start of the line is the frequency at which the event fires, followed by the action to be taken. In this example, `0 * * * *` results in the job (task) being fired once when minute = 0, thus the top of every hour. The asterisks signify "don't care" for the choice of hour, day of month, month and day of week respectively.


### Check the syslog

The success or otherwise of the tasks can be confirmed by reviewing the syslog file at /var/log/syslog:

```text
sudo nano /var/log/syslog
```

If there are any errors in the two Transfer scripts, these will be captured in the syslog. The time and date are down the left hand side, with the most recent events at the bottom of the file.

### Check gunicorn.error

The intvlm8r's main log file "gunicorn.error" will also log issues that may arise with the process of transferring from the camera to the Pi. The time and date are down the left hand side, with the most recent events at the bottom of the file.

```text
sudo nano ~/www/gunicorn.error
```
&nbsp;<br>

[Top](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/troubleshooting.md#troubleshooting)

<hr/>
<br>
