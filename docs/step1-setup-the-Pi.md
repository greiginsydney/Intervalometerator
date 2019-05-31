# Setup the Pi

If you're starting from scratch, start here at Step 1.


1. Prepare the memory card with the latest [Rasbian Stretch](https://www.raspberrypi.org/downloads/raspbian/) image.
2. Add HDMI, power and keyboard connections and turn it on. (You don't need a mouse for this, but add one if you're feeling so inclined).
3. The boot process ends at a login screen. The default credentials are `pi` / `raspberry`.
4. Login.
5. Now we'll perform the basic customisation steps:
6. Run `sudo raspi-config`.
7. Select `(4) Localisation Options` then:
    * `(I3) - change keyboard layout`
    I've never need to do anything but accept the defaults here. I found the Pi stopped responding for >10s after selecting "no compose key", so just wait for it and it will take you back to the main page.
8. Return to (4) and set `(I2) the timezone`. Select the appropriate options and you'll be returned to the menu.
9. Select `(5) - Interfacing Options`
    * `(P2) Enable SSH` and at the prompt "Would you like the SSH server to be enabled?" change the selection to `<Yes>` and hit return, then return again at the `OK`.
10. Return to `(5) - Interfacing Options`
    * `(P5)Enable I2C` and at the prompt "Would you like the ARM I2C interface to be enabled?" change the selection to `<Yes>` and hit return, then return again at the `OK`.
    
> Micro SD cards come in some large sizes these days, and if you want to keep backups of the photos off the camera, you'll probably want a card larger than the standard 32G limit of FAT. If you've started with a standard FAT format, this next step lets you expand the disk to consume the whole card. This is a good thing.  
In so doing however, your average Windows PC will no longer be able to read the card. Check out "<a href="https://ext2-volume-manager.en.lo4d.com/" target="_blank">Ext2 Volume Manager</a>" as a way to get around this. If you're at all uncertain, skip step 11, but be aware that the number of images you can store on the Pi will be limited.

11. Select `(7) Advanced Options` and select `(A1) expand filesystem`, allowing access to the whole card, then hit return again at the `OK`.
12. If you're building this onto a Pi with a wired network connection instead of WiFi, skip the next step. Resume at Step 14.
13. Select `(2) Network Options` and `WiFi`. At this stage we'll be a wifi *client*. When prompted:
    * Select your country
    * Enter the local SSID and passphrase (password). Note that the Pi Zero W's radio is limited to 2.4G, so any attempts to connect to a 5G network will fail.
14. Navigate to `Finish` and DECLINE the prompt to reboot.
15. Run `ifconfig`. In the output, look under "eth0" for wired and "wlan0" for WiFi. There should be a line starting with "inet" followed by an IP address. The absence of this means you're not on a network.

16. Assuming success above, you'll probably want to set a static IP. If you're OK with a dynamic IP (or at least are for the time being) jump to Step 18.
17. Run `sudo nano /etc/dhcpcd.conf`. Add the lines highlighted, customising the addresses to suit your network:

```txt
interface wlan0
static ip_address=192.168.44.1/24
static routers=192.168.44.254
static domain_name_servers=192.168.44.254
```

18. Set a hostname with `sudo hostname <YourNewHostname>`
19. Reboot the Pi to pickup its new IP address and lock in all the changes made above, including the change to the hostname: `sudo reboot now`

20. After it reboots, check it's on the network OK by typing `ifconfig` and check the output now shows the entries you changed in Step 18.
(Alternatively, just see if it responds to pings and you can SSH to it on its new IP).

## Remote config via SSH

At this point I abandoned the keyboard and monitor, continuing the config steps from my PC.

21. SSH to the Pi using your preferred client. If you're using Windows 10 you can just do this from a PowerShell window: `ssh <TheIpAddressFromStep18> -l pi` (Note that's a lower-case L).
22. You should see something like this:
```txt
The authenticity of host '192.168.44.1 (192.168.44.1)' can't be established.
ECDSA key fingerprint is SHA256:Ty0Bw6IZqg1234567899006534456778sFKT6QakOZ5PdJk.
Are you sure you want to continue connecting (yes/no)?
```
23. Enter `yes` and press Return
24. The response should look like this:
```txt
Warning: Permanently added '192.168.44.1' (ECDSA) to the list of known hosts.
pi@192.168.44.1's password:
```
25. Enter the password and press Return.
26. It's STRONGLY recommended that you change the password. Run `passwd` and follow your nose.

#### Here's where all the software modules are installed. This might take a while:

27. `sudo apt-get update && sudo apt-get upgrade -y`
28. `sudo reboot now`
29. Your SSH session will end here. Wait for the Pi to reboot, sign back in again and continue:
30. `sudo apt-get install python-pip python-flask -y`
31. `sudo pip install flask flask-bootstrap flask-login gunicorn configparser`
32. `sudo apt-get install nginx nginx-common supervisor python-dev python-psutil -y`
33. `sudo apt-get install libgphoto2-dev -y`
> If the above doesn't install or throws errors, run `apt-cache search libgphoto2` & it should reveal the name of the "development" version, which you should substitute back into your repeat attempt at this step.

34. `sudo pip install -v gphoto2`
35. `sudo apt-get install libjpeg-dev -y`
36. `sudo pip install -v pillow`
37. `sudo apt-get install python-smbus i2c-tools -y`
38. We don't want Bluetooth, so uninstall it<sup>[1](#uninstallbluetooth)</sup>:
    * `sudo apt-get purge bluez -y`
    * `sudo apt-get autoremove -y`

39. `sudo apt autoremove`
40. `sudo apt-get clean`
41. `sudo reboot now`


## Let's do some tests!

### I2C
At this stage GPhoto-py and the I2C bus should be working - at least from the Pi's perspective - so now's a good time to check them.
> The I2C config steps are still to come, so even if the Arduino's plugged in and running it probably won't respond, so don't be too concerned.

42. This tests the I2C is at least running in the Pi. Run `sudo i2cdetect -y 1`
43. The output should look like this:
```txt
0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```
### Camera

44. Now plug a camera into the USB port. (If you still have the monitor and keyboard plugged in, these can be discarded now).
45. Change directory to where python-gphoto2 is: `cd /usr/local/share/python-gphoto2/examples`
46. If you run `python camera-summary.py` it should see your camera and report an output like this:

```txt
pi@intervlm8r:/usr/local/share/python-gphoto2/examples $ python camera-summary.py
WARNING: gphoto2: (ptp_list_folder_eos [library.c:7342]) storage 0xffffffff, but handle 0x00000000?
Summary
=======
Manufacturer: Canon Inc.
Model: Canon EOS 60D
  Version: 3-1.1.0
  Serial Number: 123456789123456789123456789
Vendor Extension ID: 0xb (2.0)

Capture Formats: JPEG
Display Formats: Association/Directory, Script, DPOF, MS AVI, MS Wave, JPEG, CRW, Unknown(b103), Unknown(bf02), Defined Type, Unknown(b104), Unknown(b105)

Device Capabilities:
        File Download, File Deletion, File Upload
        No Image Capture, No Open Capture, Canon EOS Capture, Canon EOS Shutter Button

Storage Devices Summary:
store_00020001:
        StorageDescription: SD
        VolumeLabel: None
        Storage Type: Removable RAM (memory card)
        Filesystemtype: Digital Camera Layout (DCIM)
        Access Capability: Read-Write
        Maximum Capability: 31902400512 (30424 MB)
        Free Space (Bytes): 31588155392 (30124 MB)
        Free Space (Images): -1

Device Property Summary:
Property 0xd402:(read only) (type=0xffff) 'Canon EOS 60D'
Property 0xd407:(read only) (type=0x6) 1
Property 0xd406:(readwrite) (type=0xffff) 'Unknown Initiator'
Property 0xd303:(read only) (type=0x2) 1
Battery Level(0x5001):(read only) (type=0x2) Enumeration [100,0,75,0,50] value: 75% (75)

Abilities
=========
model: Canon EOS 60D
status: 0
port: 4
speed: []
operations: 57
file_operations: 10
folder_operations: 14
usb_vendor: 1193
usb_product: 12821
usb_class: 0
usb_subclass: 0
usb_protocol: 0
library: /usr/lib/arm-linux-gnueabihf/libgphoto2/2.5.12/ptp2
id: PTP
device_type: 0

pi@intervlm8r:/usr/local/share/python-gphoto2/examples $
```

47. If you're feeling so inclined, experiment with some of the sample files in that directory. Don't bother with any of the "-gui" ones, as they're not going to work on the Pi.


## Build a Website

Here's where you start to build the website. This process is largely a copy/mashup of these posts.<sup>[2](#deployflask)</sup> <sup>[3](#pythonflask)</sup> <sup>[4](#serveflask)</sup>

48. `cd ~`
49. Create some sub-directories to keep the various components separate from each other:
`mkdir photos && mkdir preview && mkdir thumbs && mkdir www`
53. `cd www`
54. `mkdir static && mkdir templates`
56. Now create a 'symbolic link' (a shortcut) to the photos, preview and thumbs folders so they appear in the path for the webserver to access them:
	 `ln -s ~/photos ~/www/static && ln -s ~/preview ~/www/static && ln -s ~/thumbs ~/www/static`
57. Check those appeared OK. (On my machine they show in *light* blue, where normal sub-folders are dark blue):
```txt
cd ~/www/static
ls
```
58. Now copy the script and web files across. (I used WinSCP):
59. Into the "static" folder, copy the "main.css" file & the "favicon.ico".
60. Into the "templates" folder, copy the 7 HTML files (main, index, camera, thumbnails, intervalometer, transfer & system).
61. Into the "www" folder, copy the 4 ".py" files (intvlm8r.py, cameraTransfer.py, setTime.py & wsgi.py).
62. Into /home/pi/ copy the 3 ".service" files, plus "hostapd.conf" & "intvlm8r". (We'll move them to their final locations in forthcoming steps)

63. `sudo chown -R pi:www-data /home/pi`

64. "nginx" (our web server) should already be running. If you browse to the Pi now (on port 80) you'll see a holding page: "Welcome to nginx!"

65. We've not linked nginx to Gunicorn (our HTTP server), but this should run without error and you should then be able to browse to the invtlm8r site on port 5000: 
```
cd ~/www
gunicorn --bind 0.0.0.0:5000 wsgi:app
```
(Ctrl-C to escape this).
> If this fails with `ImportError: No module named wsgi`, make sure you ran the command from the /www/ directory, and that it contains the wsgi.py file copied in from Step 61.

66. Now we create a "service" that will run the website/script. Assuming the file 'intvlm8r.service' (provided as part of the repo) is in the home directory, move it to /etc/systemd/system/ with this:
`sudo mv ~/intvlm8r.service /etc/systemd/system/intvlm8r.service`

67. `sudo systemctl start intvlm8r`
68. This command sets the intvlm8r Gunicorn service to start on boot: `sudo systemctl enable intvlm8r`
69. Now check its status: `sudo systemctl status intvlm8r`.
70. You should see something like this: look for the "Active: active (running)":
```txt
● intvlm8r.service - Gunicorn instance to serve intvlm8r
   Loaded: loaded (/etc/systemd/system/intvlm8r.service; enabled; vendor preset: enabled)
   Active: active (running) since Sat 2018-11-24 13:44:15 AEDT; 20s ago
 Main PID: 805 (gunicorn)
   CGroup: /system.slice/intvlm8r.service
           ├─805 /usr/bin/python /usr/local/bin/gunicorn --workers 3 --reload --log-level=debug --log-file /home/pi/www/gunicor
           ├─811 /usr/bin/python /usr/local/bin/gunicorn --workers 3 --reload --log-level=debug --log-file /home/pi/www/gunicor
           ├─813 /usr/bin/python /usr/local/bin/gunicorn --workers 3 --reload --log-level=debug --log-file /home/pi/www/gunicor
           └─815 /usr/bin/python /usr/local/bin/gunicorn --workers 3 --reload --log-level=debug --log-file /home/pi/www/gunicor

Nov 24 13:44:15 raspberrypi systemd[1]: Started Gunicorn instance to serve intvlm8r.
```
71. Type `Q` to quit.
72. If however your output looks like this, you've hit a permissions problem (in this case writing to the log file). Re-check the permissions steps from earlier:

```txt
● intvlm8r.service - Gunicorn instance to serve intvlm8r
   Loaded: loaded (/etc/systemd/system/intvlm8r.service; enabled; vendor preset: enabled)
   Active: failed (Result: exit-code) since Sat 2018-10-20 15:30:07 AEDT; 30s ago
 Main PID: 1113 (code=exited, status=1/FAILURE)

Oct 20 15:30:00 intervlm8r systemd[1]: Started Gunicorn instance to serve intvlm8r.
Oct 20 15:30:06 intervlm8r gunicorn[1113]: Error: Error: '/home/pi/www/gunicorn.error' isn't writable [IO
Oct 20 15:30:07 intervlm8r systemd[1]: intvlm8r.service: Main process exited, code=exited, status=1/FAILURE
Oct 20 15:30:07 intervlm8r systemd[1]: intvlm8r.service: Unit entered failed state.
Oct 20 15:30:07 intervlm8r systemd[1]: intvlm8r.service: Failed with result 'exit-code'.
```

73: Assuming the file 'intvlm8r' (provided as part of the repo) is in the home directory, move it to /etc/nginx/sites-available/ with this:
`sudo mv ~/intvlm8r /etc/nginx/sites-available/intvlm8r`

74. `sudo ln -s /etc/nginx/sites-available/intvlm8r /etc/nginx/sites-enabled`

75. Given you (presumably) want to run on Port 80, you need to move the Default site off that port.
76. Run `sudo nano /etc/nginx/sites-enabled/default` and:
    * change the port 80 references to 8080 (or something other than 80)
    * comment out the "root" line and replace it, as shown here
    * add the new lines to "location" so it looks like this
    
```txt
listen 8080 default_server;
listen [::]:8080 default_server;
#root /var/www/html;
root ~/www/templates;
	location / {
		# First attempt to serve request as file, then
		# as directory, then fall back to displaying a 404.
		try_files $uri $uri/ =404;
		include proxy_params;
		proxy_pass http://unix:/home/pi/www/intvlm8r.sock;
	}
```

77. Test your progress with `sudo nginx -t`. The output should looks like this. If not, re-check the above step before continuing:
```txt
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

78. Now restart nginx to pick up the new config: `sudo systemctl restart nginx`

79. As you did with the Gunicorn service earlier, you want to check its status: `sudo systemctl status nginx.service`.
80. You should again see a status that's "Active: active (running)". If not, re-check your steps here.
81. If you now browse to the site on Port 80 it should respond with the intvlm8r's home-page, not the default page that showed at Step 64.

> If you get a "502 Bad Gateway" that's usually indicative of a permissions problem<sup>[1](#502badgateway)</sup>. Check out the "access.log" and "error.log" files at /var/log/nginx. (Don't burn a lot of effort here without first giving it a cleansing reboot - we've done a lot!)

## Startup Tasks
### NTP

82. If your Pi will have no network connectivity once it's deployed, it will need its real time clock set each time it boots (as the clock is volatile - it's not battery-backed). If you have connectivity, skip the next steps and resume at Step 87.

83. Create a service for the time sync. This runs once when-ever the Pi boots, reading the real time from the Arduino and then using this to set its own internal clock. Assuming the file 'setTime.service' (provided as part of the repo) is in the home directory, move it to /etc/systemd/system/ with this:
`sudo mv ~/setTime.service /etc/systemd/system/setTime.service`

84. `sudo chmod 644 /etc/systemd/system/setTime.service`
85. `sudo systemctl enable setTime.service`

86. Should your Pi ever have intermittent network connectivity - even if it's only on the bench when you're building it - it's going to automatically suck the real-time from debian.pool.ntp.org, which will potentially confuse it and/or you<sup>[6](#timedatectl)</sup>. To kill this (and so you KNOW the Arduino is the Pi's authoritative clock-source), run:
* `sudo systemctl disable systemd-timesyncd` to stop it launching at boot, and 
* `sudo systemctl stop systemd-timesyncd` to stop it NOW.

### Camera Transfer - Script

87. Now create a service for the backup script. This runs once when the Pi boots, copying any new images from the camera to the Pi. Assuming the file 'cameraTransfer.service' (provided as part of the repo) is in the home directory, move it to /etc/systemd/system/ with this:
`sudo mv ~/cameraTransfer.service /etc/systemd/system/cameraTransfer.service`

88. Only do this step if you SKIPPED the "setTime" steps above. You now need to break a dependency baked into the cameraTransfer.service file. Edit this (with `sudo nano /etc/systemd/system/cameraTransfer.service`) to remove the reference to setTime.service. Change the "After=" line so it looks like this:

`After=intvlm8r.service`


89. `sudo chmod 644 /etc/systemd/system/cameraTransfer.service`
90. `sudo systemctl enable cameraTransfer.service`

### Camera Transfer - Cron Job

If your setup will be powered by a mains supply you may choose to leave the Pi running permanently. If that's the case, the above camera transfer script will never run, as it only executes when the Pi boots. To resolve this, we create a 'cron' job that runs every hour (or at a frequency you prefer) to trigger a run of the script. You can skip these steps if you're building for an off-grid or low-power setup. Jump to Step 99.

91. `crontab -e` will edit this user's 'crontab' file. You should receive this prompt:
```txt
no crontab for pi - using an empty one

Select an editor.  To change later, run 'select-editor'.
  1. /bin/ed
  2. /bin/nano        <---- easiest
  3. /usr/bin/vim.tiny
  
Choose 1-3 [2]:
```
92. Select your preferred editor (1, 2 or 3) and press return. (I went with nano.)
93. Add this line to the bottom of the file:
`0 * * * * /usr/bin/python /home/pi/www/cameraTransfer.py`

The first 5 fields represent minute, hour, day of month, month & day of week, so as shown this task will execute every day at the top of every hour.

94. Save and exit the editor.
95. Logging the cron job will be beneficial, so enable that with `sudo nano /etc/rsyslog.conf`
96. Scroll down the file until you reach this line:
`#cron.*                          /var/log/cron.log`
97. Delete the leading '#' to un-comment the line, then save and exit the editor.
98. You can confirm the cron service is running with `sudo service cron status`. It should output something like this:
```txt
● cron.service - Regular background program processing daemon
   Loaded: loaded (/lib/systemd/system/cron.service; enabled; vendor preset: enabled)
   Active: active (running) since Thu 2018-12-27 12:25:30 AEDT; 3 months 27 days ago
     Docs: man:cron(8)
 Main PID: 266 (cron)
   CGroup: /system.slice/cron.service
           └─266 /usr/sbin/cron -f

Apr 25 08:17:01 raspberrypi CRON[10604]: pam_unix(cron:session): session closed for user root
Apr 25 09:00:01 raspberrypi CRON[10636]: pam_unix(cron:session): session opened for user pi by (uid=0)
Apr 25 09:00:01 raspberrypi CRON[10640]: (pi) CMD (/usr/bin/python /home/pi/www/cameraTransfer.py)
Apr 25 09:00:01 raspberrypi CRON[10636]: pam_unix(cron:session): session closed for user pi
Apr 25 09:17:01 raspberrypi CRON[10648]: pam_unix(cron:session): session opened for user root by (uid=0)
Apr 25 09:17:01 raspberrypi CRON[10652]: (root) CMD (   cd / && run-parts --report /etc/cron.hourly)
```
> This example was captured some time AFTER the cron job was created, and so it's showing that the task has previously run. You are unlikely to see the bottom 6 lines looking like this straight away. If you're concerned or curious, repeat this step after the Pi has ticked over an hour.

## Continue with the Pi/Arduino Interfacing

Now the web-server is up and running there are a few settings to be made in the Pi to establish the interfacing between it and the Arduino.

99. Fine-tune some of the config settings with `sudo nano /boot/config.txt`
100. Add the following text to the bottom of the file. (It might already be there, but possibly commented-out):
```txt
dtparam=i2c1=on
#This slows the bus, otherwise it's too fast for the poor 8MHz Ardy. (Feel free to change to "100000" or delete the comma and the baudrate command if you don't have this restriction)
dtparam=i2c_arm=on,i2c_arm_baudrate=40000
```
101. You can paste the following lines in verbatim:
```txt
#The intervalometerator has no need for bluetooth:
dtoverlay=pi3-disable-bt

#This kills the on-board LED (to conserve power):
dtparam=act_led_trigger=none
dtparam=act_led_activelow=on

#This sets up the ability for the Arduino to shut it down:
dtoverlay=gpio-shutdown,gpio_pin=17,active_low=1,gpio_pull=up

#Set GPIO27 to follow the running state: it's High while running and 0 when shutdown is complete. The Arduino will monitor this pin.
dtoverlay=gpio-poweroff,gpiopin=27,active_low
```

102. Having saved this file, `sudo reboot now`.
103. If you now repeat the I2C test from earlier (`sudo i2cdetect -y 1`) - and assuming the Arduino's up and running, connected - the bus should report a response from device 4:

```txt
0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- 04 -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

104. You're in business! 

## Next steps are:
- Add an SSL certificate:
	- [Use Lets Encrypt](/docs/step2-setup-the-Pi-lets-encrypt.md)
	- [Public or Private PKI](/docs/step2-setup-the-Pi-public-or-private-pki.md)
- [Setup the Pi as a Wifi Access Point](/docs/step3-setup-the-Pi-as-an-access-point.md)

<br>
<hr >

<a name="uninstallbluetooth">1</a>: [Disabling BlueTooth](https://scribles.net/disabling-bluetooth-on-raspberry-pi/)

<a name="deployflask">2</a>: [Deploy flask app with nginx using gunicorn and supervisor](https://medium.com/ymedialabs-innovation/deploy-flask-app-with-nginx-using-gunicorn-and-supervisor-d7a93aa07c18)

<a name="pythonflask">3</a>: [Python Flask + nginx + gunicorn](https://gist.github.com/xaratustrah/0e648a0dca74c661c1a1c78acbd5e224)

<a name="serveflask">4</a>: [How To Serve Flask Applications with Gunicorn and Nginx on Ubuntu 16.04](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-16-04)

<a name="502badgateway">5</a>: [502 BAD Gateway](https://stackoverflow.com/questions/39919053/django-gunicorn-sock-file-not-created-by-wsgi)

<a name="timedatectl">6</a>: [Raspbian Jessie Systemctl TimeDateCtl replacement for NTP](https://www.raspberrypi.org/forums/viewtopic.php?t=178763)
