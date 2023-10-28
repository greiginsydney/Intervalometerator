# Setup remote.it

In deployments where the intvlm8r has no access to a permanent WiFi network, remote administration requires a 4G/5G "dongle" in conjunction with an outbound VPN service such as [remote.it](https://www.remote.it/).

Before proceeding you'll need a 4G/5G dongle, **and a means of powering it**.

This page documents the steps required to setup remote.it.

- [4G/5G dongle](#4g5g-dongle)
- [Powering the dongle](#powering-the-dongle)
- [Install remote.it](#install-remoteit)
- [Pair the Pi and the dongle](#pair-the-pi-and-the-dongle)


<br/>
<hr />


## 4G/5G dongle

The term's a bit of a misnomer, but when we refer to a 4G/5G dongle, we're talking about a small device that houses a carrier's SIM (or equivalent), establishes a connection to the carrier, and also creates a WiFi network to which your client devices connect in order to access the internet. The device is typically powered by a USB "A" connector mounted on one end. The USB connector is used for power only; there is no data connection to the host.

The Huawei E8372h is a typical example:
<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180671760-51e3bacd-3ed2-4e25-9551-c93a4f1999a5.png" width="60%">
</p>

Accompanying the dongle somewhere should be the SSID and key/password for its WiFi network. You'll need those shortly.

[Top](#setup-remoteit)
<hr />

## Powering the dongle

You have a couple of options for powering the dongle:

### Permanently power it

Pros:
- the intvlm8r is always online for remote admin

Cons:
- you need a permanent 5V source for the dongle. Some solar chargers have USB outlets, otherwise you'll need a separate 12V->5V converter
- the extra current consumption may require you install a larger solar panel, charger and battery. Of course if you have local mains power this is not a concern
- maintaining the VPN tunnel to remote.it 24x7x365 will presumably consume more of your data allowance

### Power it from the intvlm8r PCB

The intvlm8r PCB supplies 5V to the Raspberry Pi Zero via its GPIO pins, and the Pi's dedicated "PWR IN" USB socket is not used.

This socket is wired directly in parallel with the power pins on the GPIO, so instead of using it as an input, you can use it as an *output* by plugging the dongle into this socket (via another USB adapter).

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180677808-3810c9f2-5ec3-47cb-a1fc-650d1f395839.png" width="50%">
</p>

<br>

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180698157-cdb8fd3b-788c-4c0b-aaf8-af3bf3b67350.png" width="50%">
</p>


The caveat here is that the specified on-board 5V power supply doesn't have the capacity to run the Pi *plus* the dongle, so it will need to be upgraded.

The [Pololu 2858 (aka D24V22F5)](https://www.pololu.com/product/2858) is recommended. This is demonstrated on the "Advanced Config" page under ["Other Pi Models"](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/advancedConfig.md#other-pi-models).

Pros:
- minimum additional current consumption
- "least pain" upgrade/retrofit path

Cons:
- if you've already assembled the PCB (or bought a pre-assembled one) you'll need to upgrade the on-board 5V regulator to a higher-powered unit
- the intvlm8r is only accessible each day during the "Pi on time" maintenance window specified on the /system page

### Use the intvlm8r to switch a separate power supply

One contributor used a "MOSFET module" from eBay as a solid state relay. It's triggered by the Raspberry Pi's 5V power supply (using the same "PWR IN" USB socket described above) and switches a separate power supply for the dongle.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180699325-a131a63d-eb6b-4070-b585-18c2cda2c793.png" width="30%">
</p>

Here's a similar device on [Tindie](https://www.tindie.com/products/8086net/usb-power-switch/):
<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/215303845-7d13e826-17cf-455f-be8c-82b95345eea5.png" width="30%">
</p>


Pros:
- no need to modify the existing intvlm8r PCB
- easily removed if no longer required

Cons:
- a little more complicated
- still requires an outboard USB power supply to power the dongle

[Top](#setup-remoteit)
<hr />

## install remote.it

**This process was last confirmed accurate on October 29th, 2023.**

1. Visit [remote.it's homepage](https://www.remote.it/) and click the blue "Get Started" button in the top right. Follow your nose to create a new login.
2. Login.
3. Click the blue "+" button in the top left, then select "Raspberry Pi":

<p align="center">
  <img src="https://github.com/greiginsydney/Intervalometerator/assets/11004787/07304308-80c9-4802-9c4c-5b9835a9f9a5" width="40%">
</p>




4. Use the highlighted icon to copy the registration text to the clipboard:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180706135-611dad5b-9661-4dc3-b412-aa533b75ef4f.png" width="60%">
</p>

Leave the browser window open - we're not finished with it yet.

5. Paste the above registration text into an SSH session to the Raspberry Pi and hit return:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180707447-187b5dff-18cf-41f4-8646-cddf2872d976.png" width="80%">
</p>

This process installs Remote.it on the Pi which then launches and establishes the initial connection back to the remote.it hosts.

6. If the previous step completes successfully, your remote.it webpage will update with the details of the new device:

<p align="center">
<img src="https://github.com/greiginsydney/Intervalometerator/assets/11004787/b603b99f-ad11-4861-b039-2c3766fb5b40" width="80%">
</p>

7. Congratulations. So far so good. By default, remote.it creates an SSH "service", so you have command-line access to the Pi. Next is to add a web (http) service. This enables you to launch a web-session to the intvlm8r's website. Click the highlighted "+", then click Save to accept the defaults:

<p align="center">
<img src="https://github.com/greiginsydney/Intervalometerator/assets/11004787/ef08a45b-2182-460a-a195-cf7331880d42" width="80%">
</p>

(If you've already put an SSH certificate on the Pi, you might choose HTTPS instead here.)

8. To double-check we're good to proceed, execute the install script with the "remoteit" switch `sudo -E ./setup.sh remoteit`. The output should include the following:

<p align="center">
<img src="https://github.com/greiginsydney/Intervalometerator/assets/11004787/7d7b3a9a-4388-477d-98fa-a4c71d6f1594" width="80%">
</p>

(If you're still running the legacy version, you probably should upgrade. That process is documented here: https://support.remote.it/hc/en-us/articles/360051668711-Updating-the-remoteit-or-connectd-packages-using-a-remote-it-SSH-connection.)
<br>

[Top](#setup-remoteit)
<hr />


## Pair the Pi and the dongle

If you're running the Pi as an Access Point (AP), you'll need to turn it into a WiFi _client_ so it can connect to the dongle.

The first thing we'll do though is connect it to your local WiFi network so you can still continue to access it on the bench.

If the Pi is already a WiFi client, skip to Step 13.

10. Follow the process shown in [Un-make AP](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step3-setup-the-Pi-as-an-access-point.md#un-make-ap) to join your local WiFi network.

11. At the prompt `Do you want to assign the Pi a static IP address?` choose No and let your local DHCP server allocate it an address.

> Beware here that without a monitor attached to the Pi or a means to query your local DHCP server, you risk losing connectivity with the Pi after the reboot in the next step, because you won't know its new IP address. Tread carefully.

12. Reboot when prompted.

13. Now for the sneaky bit: the Pi can be set with the details of *multiple* WiFi networks, so when it's on the bench it will connect to your local WiFi, and when it's in the field it will connect to the dongle. For that we'll need to edit `wpa_supplicant.conf`:

```
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

All you need to do is duplicate the existing "network" block, like shown in the red box, and add some Priority values:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/181138742-c1ad3111-81bc-400f-bafc-d9212aaa5292.png" width="80%">
</p>

When in the presence of BOTH WiFi networks, the Pi will connect to the network with the numerically higher value, in this case "MyLocalWiFiSSID".

14. Save the file and you're done! Reboot for it to pick up all the new values and give it a test.


<br>

[Top](#setup-remoteit)
<hr />




