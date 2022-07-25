# Setup remote.it

In deployments where the intvlm8r has no access to a permanent WiFi network, remote administration requires a 4G/5G "dongle" in conjunction with an outbound VPN service such as [remote.it](https://www.remote.it/).

Before proceeding you'll need a 4G/5G dongle, **and a means of powering it**.

This page documents the steps required to setup remote.it.

- [4G/5G dongle](#4g5g-dongle)
- [Powering the dongle](#powering-the-dongle)
- [Install remote.it](#install-remoteit)
- [Prepare the intvlm8r](#prepare-the-intvlm8r)


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
- the intvlm8r is always online for remote admin.

Cons:
- you need a permanent 5V source for the dongle. Some solar chargers have USB outlets, otherwise you'll need a separate 12V->5V converter.
- the extra current consumption may require you install a larger solar panel, charger and battery. Of course if you have local mains power this is not a concern.
- maintaining the VPN tunnel to remote.it 24x7x365 will presumably consume more of your data allowance.

### Power it from the intvlm8r PCB

The intvlm8r PCB supplies 5V to the Raspberry Pi Zero via its GPIO pins, and the Pi's dedicated "PWR IN" USB socket is not used.

This socket is wired directly in parallel with the power pins on the GPIO, so instead of using it as an input, you can use it as an *output* by plugging the dongle into this socket (via another USB adapter).

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180677808-3810c9f2-5ec3-47cb-a1fc-650d1f395839.png" width="60%">
</p>

<br>

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180698157-cdb8fd3b-788c-4c0b-aaf8-af3bf3b67350.png" width="60%">
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
<img src="https://user-images.githubusercontent.com/11004787/180699325-a131a63d-eb6b-4070-b585-18c2cda2c793.png" width="40%">
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

1. Visit [remote.it's homepage](https://www.remote.it/) and click the blue "Get Started" button in the top right. Follow your nose to create a new login.
2. Login.
3. Click the blue "+" button in the top left, then select "Raspberry Pi" from the popup menu:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180705819-941aba10-6217-4717-98d0-0d51b8f8239a.png" width="40%">
</p>

4. Use the highlighted icon to copy the registration text to the clipboard:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180706135-611dad5b-9661-4dc3-b412-aa533b75ef4f.png" width="80%">
</p>

Leave the browser window open.

5. Paste the above registration text into an SSH session to the Raspberry Pi and hit return:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180707447-187b5dff-18cf-41f4-8646-cddf2872d976.png" width="80%">
</p>

This process installs Remote.it on the Pi which then launches and establishes the initial connection back to the remote.it hosts.

6. If the previous step completes successfully, your remote.it webpage will update with the details of the new device:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180712194-4fe88e21-f9cf-40a0-bb82-634daf9a291c.png" width="80%">
</p>

7. Congratulations. So far so good. Next is to add a web (http) "service". This enables you to launch a web-session to the intvlm8r's website. Click the highlighted "+", then click Save to accept the defaults:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180708852-0ca88325-877b-4705-9212-8105de781176.png" width="80%">
</p>

8. The default remote.it install process **breaks** the intvlm8r, so we need to run the install script to fix this. Execute `sudo -E ./setup.sh remoteit`:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180711369-358c61f4-56f8-47db-816d-2454ab7f0665.png" width="80%">
</p>

9. To double-check we're good to proceed, execute the install script with the "test" switch `sudo -E ./setup.sh test`. The output should include the following:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180711278-59c5fcfa-0cae-494d-856d-132a253f4ea8.png" width="80%">
</p>









<br>

[Top](#setup-remoteit)
<hr />


## Prepare the intvlm8r

<br>

[Top](#setup-remoteit)
<hr />




