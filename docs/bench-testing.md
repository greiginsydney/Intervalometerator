# Bench Testing

Having fully assembled the board, it's time to test it out and make sure it's working as expected.

This page assumes:
* All tests on the [PCB Assembly](docs\pcb-assembly.md) page passed
* Both micro-controllers are programmed
* Your PC and the Pi are on the same network, and that you know the Pi's IP address
* The camera is plugged in (both the remote cable _and_ USB)
* (optional) You have an HDMI monitor plugged into the Pi
* PCB links/jumpers are:
    * J1 - the lower two pins are linked
    * J2 - the top two and lower two pins are linked
    * MC - these pins are linked
    * Reed - there is no jumper on the Reed terminals, or any connected switch is open-circuit
    * J3 & J4 - each has diagonal link placement, e.g. on one the upper pins are connected, and on the other the lower two pins are connected.

## Power-on

1. Apply power. A number of things will happen in quick succession:

    * The green "Awake" LED on the top edge of the board should flash either four or eight times:
        * Four times is a 'healthy' power-on of the Arduino, confirming the time was successfully read from the RTC. Normal operation will resume. If you powered the board at the end of [PCB Assembly](docs\pcb-assembly.md) and the Arduino was programmed, it is expected for the LED to flash four times now.
        * Eight times is an 'unhealthy' power-on of the Arduino. It indicates there was a failure reading from the RTC, most likely to be the result of a flat battery, or the very first time the board is powered. An emergency program kicks in at this stage, as the Arduino has no idea if it's day or night. It will shoot a photo every 15 minutes until the clock is set/reset.
    * The green LED will go out for two seconds, then flash three times, before remaining lit, but at a lesser intensity. On power-up the Arduino wakes the Pi, and the "dim" LED is in fact it toggling with every pass through the main program loop.

2. If the LED didn't flash at all, check the 3.3V supply is OK and make sure the Arduino is seated correctly. Failure here probably warrants reconnecting the programming header and interrogating the Arduino.

3. Regardless of the flash count, the board will trigger a photo on power-up. If that didn't happen, check the camera is plugged in OK and powered on. You should be able to wake the camera by shorting pins 4 & 5 of the right-hand opto with a small screwdriver, and take a photo by doing same to the left-hand opto.
    
4. When the Maintenance Connector pins are linked the LED will be steadily lit (or as good as) when-ever the Arduino is awake.

> In normal use, DON'T leave the MC link present, as the LED may leak sufficient light into the case to be captured in photos.

> The MC link and LED are diagnostic aids - you're welcome to customise either/both.

5. To conserve power the Arduino is normally asleep. It is woken by hardware interrupts from one of two sources: the RTC triggers an alarm, or on the falling-edge transition of the Reed pin. (A reed trigger is simulated in code on power-up.)

6. By this stage the Pi should have almost completed booting. At around the time it reaches the login prompt on the monitor it should start responding to pings.

7. If the Pi hasn't shown any sign of life on the screen, check the 5V rail. <MORE HERE>

8. Responds to pings, might give 502 bad gateway - copying images.

TEXT HERE

8. Press / activate the Reed switch. The LED will light to indicate the Arduino is awake, and your action will cause the Arduino to wake the Pi. As long as the Pi is awake, the Arduino will remain awake, so with the MC pins linked, the LED will remain on.

6. If you're inclined to wait 15 minutes, the LED will light for around 4s, the camera will take a photo, and the LED will then extinguish.

