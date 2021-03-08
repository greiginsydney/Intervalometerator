# Setup the Pi as an Access Point

## Starting from scratch?
Jump to [setup the Pi](/docs/step1-setup-the-Pi.md).

## Setup the Pi as an Access Point
You should only perform the steps here once you've completed the config steps and tested the Pi.

This process will drop it off the current WiFi network and turn it into its own network and Access Point, at which time it will lose Internet access and be unable to load new software components.

Skip this document entirely if you're NOT wanting the Pi to be a WiFi Access Point and accept client connections directly.[1][2]

## Make AP

1. Run the setup script with the "ap" attribute:
```txt
sudo -E ./setup.sh ap
```

2. The script will prompt you for all the required values. On its first run out of the box it will offer default values. These will usually be safe to use, but by all means change the SSID and WiFi password from the defaults:

```txt
Set your Pi as a WiFi Access Point. (Ctrl-C to abort)
If unsure, go with the defaults until you get to the SSID and password

Choose an IP address for the Pi        : 10.10.10.1
Choose the starting IP address for DCHP: 10.10.10.10
Choose  the  ending IP address for DCHP: 10.10.10.100
Set the appropriate subnet mask        : 255.255.255.0
Pick a nice SSID                       : Intvlm8r
Choose a better password than this     : myPiNetw0rkAccess!
Choose an appropriate WiFi channel     : 5
```

> The default radio channel #5 is valid around the world, HOWEVER you may find it congested in your area and choosing another may provide better connectivity.[3]

3. Upon completion the script will prompt for a reboot. 

```txt
WARNING: After the next reboot, the Pi will come up as a WiFi access point!
Reboot now? [Y/n]:
```

> After this reboot you'll need to connect to it on its new IP address, and you'll be again prompted to trust it.


## Next steps:
- Configure the Arduino
- Complete the physical assembly:
   - [PCB assembly](/docs/step5-pcb-assembly.md)  
- Start taking photos!

## Un-make AP

1. If at any time you want to switch the Pi from being an Access Point to being a wireless client on another network, run:
```txt
sudo -E ./setup.sh noap
```

2. The script will then prompt you to set or reconfirm the WiFi details:
```txt
Set your two-letter WiFi country code : AU
Set the network's SSID                : yourWiFiSSID
Set the network's Psk (password)      : 12345Password!
```

3. In the next step you have the option of setting a static IP address and related values. If you respond 'n' to this prompt, the Pi will request a dynamic IP address from the wireless router:
```txt
Do you want to assign the Pi a static IP address? [Y/n]: y
Choose an IP address for the Pi         : 192.168.19.123
Set the appropriate subnet mask         : 255.255.255.0
Set the Router IP                       : 192.168.19.1
Set the DNS Server(s) (space-delimited) : 192.168.19.2
```

3. Upon completion the script will prompt for a reboot. 
```txt
WARNING: After the next reboot, the Pi will come up as a WiFi *client*
WARNING: It will attempt to connect to this/these SSIDs: yourWiFiSSID
WARNING: 'sudo nano /etc/wpa_supplicant/wpa_supplicant.conf' to change

Reboot now? [Y/n]:
```

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
[3] [List of WLAN channels](https://en.wikipedia.org/wiki/List_of_WLAN_channels#2.4_GHz_(802.11b/g/n/ax))
