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
```

> The default radio channel #5 is valid around the world, HOWEVER you may find it congested in your area and choosing another may provide better connectivity.[3]

3. Upon completion the script will prompt for a reboot. 


> After this reboot you'll need to connect to it on its new IP address, and you'll be again prompted to trust it.


## Next steps:
- Configure the Arduino
- Complete the physical assembly:
   - [PCB assembly](/docs/step4-pcb-assembly.md)  
- Start taking photos!

## Un-make AP

If for some reason you want to revert this AP step, run:
```txt
sudo -E ./setup.sh noap
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
