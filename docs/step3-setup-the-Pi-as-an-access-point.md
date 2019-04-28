# Setup the Pi as an Access Point

## Starting from scratch?
Jump to [setup the Pi](/docs/step1-setup-the-Pi.md)

## Setup the Pi as an Access Point
You should only perform the steps here once you've completed the config steps and tested the Pi.

This process will drop it off the current WiFi network and turn it into its own network and Access Point, at which time it will lose Internet access and be unable to load new software components.

Skip this document entirely if you're NOT wanting the Pi to be a WiFi Access Point and accept client connections directly.[1][2]

## DHCP Server Config

In this task we'll set the WLAN/DHCP config as below. Change these values if you prefer.

Raspberry Pi's IP: 192.168.44.1<br>
First IP address it issues: 192.168.44.10<br>
Last IP address it issues: 192.168.44.20<br>
The subnet mask for this network: 255.255.255.0

1. `sudo apt-get install dnsmasq hostapd -y`
2. `sudo systemctl stop dnsmasq`
3. `sudo systemctl stop hostapd`

4. Set the static IP for the Pi: `sudo nano /etc/dhcpcd.conf`
5. Paste this to the bottom of the file:
```text
interface wlan0
   static ip_address=192.168.44.1/24
   nohook wpa_supplicant
```
6. Control-X to save and Exit the file.

7. Create a backup copy of your DHCP config before continuing: `sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig`  

8. Now create a new 'dnsmasq' file: `sudo nano /etc/dnsmasq.conf`. Paste the below config in:

```txt
interface=wlan0      # Use the require wireless interface - usually wlan0
  dhcp-range=192.168.44.10,192.168.44.20,255.255.255.0,24h
```

9. Control-X to save and Exit the file.

10. Assuming the file 'hostapd.conf' (provided as part of the repo) is in the home directory, move it to /etc/hostapd/ with this:
`sudo mv ~/hostapd.conf /etc/hostapd/hostapd.conf`

11: Edit the file to customise the SSID, radio channel and password. Make sure you DON'T use any quotes or other punctuation around the password:
`sudo nano /etc/hostapd/hostapd.conf`

12. Add the following line to the new file 'hostapd' `sudo nano /etc/default/hostapd`
```txt
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

13. Control-X to save and Exit the file.

14. `sudo service hostapd start`
15. `sudo service dnsmasq start`

16. `sudo reboot now` cleans the IP settings and brings the Pi back up as an AP.


After this reboot you'll need to connect to it on its new IP address, and you'll be again prompted to trust it.

## Next steps:
- Configure the Arduino
- Complete the physical assembly:
   - [PCB assembly](/docs/step4-pcb-assembly.md)  
- Start taking photos!


## Debugging

### Can't find the Pi's WiFi network?
- check you've chosen appropriate localisation settings in `hostapd.conf`. Don't forget the PiZero W is limited to 802.11g, the 2.4GHz frequencies [3]
- check the hostapd service is running OK: `sudo service hostapd status`
- run this debug command and look through the output for any clues:
`sudo hostapd -d /etc/hostapd/hostapd.conf`
- maybe change `hostapd.conf` to a different channel, just in case there's local congestion on the channel you've chosen? </ClutchingAtStraws>

### Can see but can't connect to the Pi's WiFi network?
- check you didn't wrap the password in `hostapd.conf` inside quotes

### Other problems
- check the dnsmasq service is running OK: `sudo service dnsmasq status`
- check the dhcpcd service is running OK: `sudo service dhcpcd status`
- is the Pi's local IP showing correctly in the wlan0 section of `ifconfig`?

<br>
<hr >

[1] [Configuring the Pi as a WiFi AP](https://github.com/SurferTim/documentation/blob/6bc583965254fa292a470990c40b145f553f6b34/configuration/wireless/access-point.md)<br>
[2] [Setting up a Raspberry Pi as an access point in a standalone network (NAT)](https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md)<br>
[3] [List of WLAN channels](https://en.wikipedia.org/wiki/List_of_WLAN_channels)
