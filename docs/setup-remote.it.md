# Setup remote.it

In deployments where the intvlm8r has no access to a permanent WiFi network, remote administration requires a "4G/5G Dongle" in conjunction with an outbound VPN service such as ["remote.it"](https://www.remote.it/).

This page documents the steps required to setup remote.it.

Before proceeding you'll need a 4G/5G dongle, **and a means of powering it**.

- [4G/5G dongle](#4g-5g-dongle)
- [Powering the dongle](#powering-the-dongle)
- [remote.it](#remote.it)
- [Prepare the intvlm8r](#prepare-the-intvlm8r)


<br/>
<hr />


## 4G/5G Dongle

The term's a bit of a misnomer, but when we refer to a 4G/5G dongle, we're talking about a small device that houses a carrier's SIM (or equivalent), establishes a connection to the carrier, and also creates a WiFi network to which your client devices connect in order to access the internet. The device is typically powered by a USB "A" connector mounted on one end. The USB connector is used for power only; there is no data connection to the host.

The Huawei E8372h is a typical example:
<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/180671760-51e3bacd-3ed2-4e25-9551-c93a4f1999a5.png" width="60%">
</p>

Accompanying the dongle somewhere should be the SSID and key/password for its WiFi network. You'll need those shortly.

[Top](#Setup-remote--it)
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

The caveat here is that the specified on-board 5V power supply doesn't have the capacity to run the Pi PLUS the dongle, so it will need to be upgraded.

The [Pololu 2858 (aka D24V22F5)](https://www.pololu.com/product/2858) is recommended.

Pros:
- minimum additional current consumption
- "least pain" upgrade/retrofit path

Cons:
- if you've already assembled the PCB (or bought a pre-assembled one) you'll need to upgrade the on-board 5V regulator to a higher-powered unit
- the intvlm8r is only accessible each day during the "Pi on time" maintenance window specified on the /system page

## remote.it

1. Visit [remote.it's homepage](https://www.remote.it/) and click the blue "Get Started" button in the top right. Follow your nose to create a new login.
2. Login.
<br>

[Top](#Setup-remote--it)
<hr />


## Prepare the intvlm8r

<br>

[Top](#Setup-remote--it)
<hr />




