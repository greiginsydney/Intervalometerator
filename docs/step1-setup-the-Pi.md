# Setup the Pi

If you're starting from scratch, start here at Step 1.


1. Prepare the memory card with the latest [Raspberry Pi OS 'Lite'](https://www.raspberrypi.org/software/operating-systems/) image.

> The ["Raspberry Pi Imager"](https://www.raspberrypi.org/software/) app can download and write the image to a memory card for you quickly and easily.

2. Add HDMI, power and keyboard connections and turn it on. (You don't need a mouse for this, but add one if you're feeling so inclined).
3. The boot process ends at a login screen. The default credentials are `pi` / `raspberry`.
4. Login.
5. Now we'll perform the basic customisation steps:
6. Run `sudo raspi-config`.
7. Select `(5) Localisation Options` then:
    * `(L3) - change keyboard layout`
    I've never needed to do anything but accept the defaults here. I found the Pi stopped responding for >10s after selecting "no compose key", so just wait for it and it will take you back to the main page.
8. Return to (5) and set `(L2) the timezone`. Select the appropriate options and you'll be returned to the menu.
9. Select `(3) - Interfacing Options`
    * `(P2) Enable SSH` and at the prompt "Would you like the SSH server to be enabled?" change the selection to `<Yes>` and hit return, then return again at the `OK`.
10. This step intentionally left blank. ;-)
    
> Micro SD cards come in some large sizes these days, and if you want to keep backups of the photos off the camera, you'll probably want a card larger than the standard 32G limit of FAT. If you've started with a standard FAT format, this next step lets you expand the disk to consume the whole card. This is a good thing.  
In so doing however, your average Windows PC will no longer be able to read the card. Check out "<a href="https://ext2-volume-manager.en.lo4d.com/" target="_blank">Ext2 Volume Manager</a>" as a way to get around this. If you're at all uncertain, skip step 11, but be aware that the number of images you can store on the Pi will be limited.

11. Select `(6) Advanced Options` and select `(A1) expand filesystem`, allowing access to the whole card, then hit return again at the `OK`.
12. Select `(1) System Options` and `(S4) Hostname` and give the Pi a recognisable hostname.
13. If you're building this onto a Pi with a wired network connection instead of WiFi, skip the next step. Resume at Step 15.
14. Select `(1) System Options` and `(S1) Wireless LAN`. At this stage we'll be a wifi *client*. When prompted:
    * Select your country
    * Enter the local SSID and passphrase (password). Note that the Pi Zero W's radio is limited to 2.4G, so any attempts to connect to a 5G network will fail.
15. Navigate to `Finish` and DECLINE the prompt to reboot.
16. Run `ifconfig`. In the output, look under "eth0" for wired and "wlan0" for WiFi. There should be a line starting with "inet" followed by an IP address. The absence of this means you're not on a network.

17. Assuming success above, you'll probably want to set a static IP. If you're OK with a dynamic IP (or at least are for the time being) jump to Step 19.
18. Run `sudo nano /etc/dhcpcd.conf`. Add the lines shown, customising the addresses to suit your network:

```txt
interface wlan0
static ip_address=192.168.44.1/24
static routers=192.168.44.254
static domain_name_servers=192.168.44.254
```
> If you have more than one DNS server, add them on the same line with each separated by a space

19. Reboot the Pi to pickup its new IP address and lock in all the changes made above, including the change to the hostname: `sudo reboot`

20. After it reboots, check it's on the network OK by typing `ifconfig` and check the output now shows the entries you added in Step 18.
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

## Here's where all the software modules are installed. This might take a while:

27. First let's make sure the Pi is all up-to-date:
```txt
sudo apt-get update && sudo apt-get upgrade -y
```

> If this ends with an error "Some index files failed to download. They have been ignored, or old ones used instead." just press up-arrow and return to retry the command. You want to be sure the Pi is healthy and updated before continuing.

28. `sudo reboot`

Your SSH session will end here. Wait for the Pi to reboot, sign back in again and continue

29. We need to install Subversion so we can download *just* the Pi bits of the repo from GitHub:
```txt
sudo apt-get install subversion -y
```
30. This downloads the repo, dropping the structure into the home directory:
```txt
svn export https://github.com/greiginsydney/Intervalometerator/trunk/Raspberry%20Pi/ ~ --force
```

> Advanced tip: if you're testing code and want to install a new branch direct from the repo, replace "/trunk/" in the link above with `/branches/<TheBranchName>/`

31. All the hard work is done by a script in the repo, but it needs to be made executable first:
```txt
sudo chmod +x setup.sh
```
32. Now run it! (Be careful here: the switches are critical. "-E" ensures your user path is passed to the script. Without it the software will be moved to the wrong location, or not at all. "-H" passes the Pi user's home directory.)
```txt
sudo -E -H ./setup.sh start
```

33. First up you'll be presented with a menu to choose which of the upload/transfer options to install:

```txt
====== Select Upload/Transfer options =======
An 'X' indicates the option will be installed

1. [X] SFTP
2. [X] Dropbox
3. [X] Google Drive

Press 1, 2 or 3 to toggle the selection.
Press return on its own to continue with the install
```

Accept the defaults just by pressing return on its own, or choose 1, 2 or 3 (then return) to de-select the options that aren't relevant to you. (You can always install them later if the need arises).

> If you choose ALL the options (the default), this step now takes **over an hour** to complete, depending on how slow your Internet connection is. (As at March 2020.) SFTP is the real time-killer here.

> If any step fails, the script will abort and on-screen info should reveal the component that failed. You can simply re-run the script at any time (up-arrow / return) and it will simply skip over those steps where no changes are required. There are a lot of moving parts in the Raspbian/Linux world, and sometimes a required server might be down or overloaded. Time-outs aren't uncommon, hence why simply wait and retry is a valid remediation action.

> If libgphoto throws errors, run `apt-cache search libgphoto2` & it should reveal the name of the "development" version, which you will need to edit back into the script before your repeat attempt at this step.

34. If all goes well, you'll be presented with a prompt to reboot:
```txt
Exited install_apps OK.
Reboot now? [Y/n]:
```
Pressing return or anything but n/N will cause the Pi to reboot.

35. After the Pi has rebooted, sign back in again and resume. The next step is to re-run the script, but with a new switch:
```txt
sudo -E ./setup.sh web
```

36. The script will now move some of the supporting files from the repo to their final homes, and edit some of the default config in the Pi. 

It will output its progress to the screen:
```txt
pi@raspberrypi:~ $ sudo -E ./setup.sh web
mkdir: created directory 'photos'
mkdir: created directory 'preview'
mkdir: created directory 'thumbs'
'intvlm8r.service' -> '/etc/systemd/system/intvlm8r.service'
'intvlm8r' -> '/etc/nginx/sites-available/intvlm8r'
```

37. You will be asked to provide a username and password for the web interface. Accept the defaults if you like, but preferably come up with your own. (You should DEFINITELY change these if the intvlm8r is connected to the Internet or a network where anyone else might find it.)

```txt
Change the website's login name: admin
Change the website's password  : password
```

38. If your Pi will have no network connectivity once it's deployed, it will need its real time clock set each time it boots (as the clock is volatile - it's not battery-backed). 

```txt
NTP Step. Does the Pi have network connectivity? [Y/n]:
```

If you respond 'n' to the prompt, the script will move the repo's "setTime.service" file to /etc/systemd/system/. This will in turn cause the provided "setTime.py" script to be run when-ever the Pi boots, reading the real time from the Arduino and then using this to set the Pi's own internal clock.

39. If all goes well, you'll be presented with a prompt to reboot:
```txt
Exited install_website OK.
Reboot now? [Y/n]:
```
Pressing return or anything but n/N will cause the Pi to reboot.

40. You're in business!  After the Pi reboots you should be able to browse to its IP address, where you'll be presented the message "You need to sign in before you can access that page!" and the login form.

41. Login with the credentials you set in Step 37. You can change those or add new login/password pairs by editing the /www/intvlm8r.py script.

## Next steps are:
- Add an SSL certificate:
	- [Use Lets Encrypt](/docs/step2-setup-the-Pi-lets-encrypt.md)
	- [Public or Private PKI](/docs/step2-setup-the-Pi-public-or-private-pki.md)
- [Setup the Pi as a Wifi Access Point](/docs/step3-setup-the-Pi-as-an-access-point.md)

<br>
<hr >
