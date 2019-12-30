# Bench Testing

Having fully assembled the board, it's time to test it out and make sure it's working as expected.

This page assumes:
* All tests on the [PCB Assembly](/docs/step5-pcb-assembly.md) page passed
* Both micro-controllers are programmed
* Your PC and the Pi are on the same network, and that you know the Pi's IP address
* The camera is plugged in (both the remote cable _and_ USB). Try to use a fresh memory card with (ideally) just one photo on it. Any more and the process of transferring the images to the Pi will bog down your testing.
* (optional) You have an HDMI monitor plugged into the Pi
* PCB links/jumpers are:
    * J1 - the lower two pins are linked
    * J2 - the top two pins are linked, and the lower two pins are linked
    * MC - these pins are linked
    * Reed - there is no jumper on the Reed terminals, or any connected switch is open-circuit
    * J3 & J4 - each has diagonal link placement, e.g. on one the upper two pins are connected, and on the other the lower two pins are connected.

## Power-on

1. Apply power. A number of things will happen in quick succession:

    * The green "Awake" LED on the top edge of the board should flash either four or eight times:
        * Four times is a 'healthy' power-on of the Arduino, confirming the time was successfully read from the RTC. Normal operation will resume. If you powered the board at the end of [PCB Assembly](/docs/step5-pcb-assembly.md) and the Arduino was programmed, it is expected for the LED to flash four times now.
        * Eight times is an 'unhealthy' power-on of the Arduino. It indicates there was a failure reading from the RTC, most likely to be the result of a flat battery, or the very first time the board is powered. An emergency program kicks in at this stage, as the Arduino has no idea if it's day or night. It will shoot a photo every 15 minutes until the clock is set/reset.
    * The green LED will go out for two seconds, then flash three times, before remaining lit, but at a lesser intensity. (On power-up the Arduino wakes the Pi, and the "dim" LED is in fact it toggling with every pass through the main program loop.)

2. If the LED didn't flash at all:
    1. Check the 3.3V supply is OK
    2. Make sure the Arduino is seated correctly, with no pins bent underneath, etc
    3. Check the LED is oriented the right way (refer the pictures and component overlay diagram)
    4. Check the right-hand resistor under J1 is 150 ohms
    5. If you socketed the Arduino:
         1. remove power
         2. remove the Arduino
         3. reapply power
         4. using a test lead or jumper wire, apply 3.3V to the **bottom** of the 150 ohm resistor immediately to the left of the Arduino. (This is the RH one underneath J1.) If the LED _still_ doesn't light, this confirms you have a hardware problem on the board. Check the LED's pointing the right way, and that you didn't put a wrong value resistor in there. (If you remove the test lead, it's safe to put your multimeter across the resistor at this point and read its resistance).
         5. If the LED _does_ light, it's pointing to an issue back into the Arduino. Remove power, replace the Arduino, reconnect the programming header and check the Arduino's happy, the code verifies and is loaded OK.

3. If you've reached this point, the LED must have flashed. Contratulations!

4. Regardless of the flash count, the board will trigger a photo on power-up. If that didn't happen, check the camera is plugged in OK and powered on. You should be able to wake the camera by shorting pins 4 & 5 of the right-hand opto with a small screwdriver, and take a photo by doing same to the left-hand opto.
    
5. When the Maintenance Connector pins are linked the LED will be steadily lit (or as good as) when-ever the Arduino is awake.

> In normal use, DON'T leave the MC jumper present, as the LED may leak sufficient light into the case to be captured in photos.

> The MC jumper and LED are diagnostic aids - you're welcome to customise either/both in the Arduino's code.

5. To conserve power the Arduino is normally asleep. It is woken by hardware interrupts from one of two sources: the RTC (signalling an alarm has fired), or on the falling-edge transition of the Reed pin - a human wakeup call. (A reed trigger is simulated in code on power-up.)

6. By this stage the Pi should have almost completed booting. At around the time it reaches the login prompt on the monitor it should start responding to pings.

7. If the Pi hasn't shown any sign of life on the screen, check the 5V test point, which should be at ~5V.
    * If it's not, check the bottom "Enable" pin on the 5V (left-hand) regulator is at 0V, and if that's reading anything higher, make sure the J1 jumper is on the bottom two pins. Removing the J1 jumper should force the regulator to start and the Pi to boot. If this is the case, it points to a problem with the Arduino's IO pins and/or programming.
    * If the 5V rail is good and there's no sign of life on the HDMI monitor, check the wire links from the Pi to the PCB are going through the correct holes, or your HDMI monitor/connection.

## Browse to the Pi

8. With the Pi now responding to pings, try and browse to it from your PC. Don't worry if it fails with an error page reporting "502 Bad Gateway". This is expected - and unavoidable - if the Pi is busy, which it will typically be immediately on boot, as it's busy trying to copy all of the images from the camera to its SD card. F5 to refresh your browser, or if there are lots of images on the camera, go make a coffee. (While images are being transferred, the red LED on the back of the Canon 6-series cameras flickers. Other cameras may provide similar on-body feedback.)

9. Assuming the website has loaded, you'll need to login before you can do or see anything. The default credentials are admin/password.

10. Having logged in you'll be presented with the home page:
    * it will report a System Date of January 1, 2019 and the time as some minutes past noon. The "Next Photo" will be 12:15, or the next 15 minute increment from the current time.
    * if the System Date is "Unknown", it's having a problem communicating with the Arduino. F5 to refresh the page, which prompts a fresh query to the Arduino. If still Unknown, check:
        * you don't have the SDA and SCL leads the wrong way 'round.
        * the wire links from the Pi to the PCB are going through the correct holes.
        * you put the wires in the right pair of holes on the Arduino. (There is another pair of holes nearby; you might have mixed them up.)
        * If you're still stumped, check the Arduino programming (although if you've made it to here, LED on, etc, it seems like it's programmed OK).
        
11. Click the hamburger icon and select System (or edit the URL to just add "/system" to the end). The System page should display.

12. Scroll to the "Set system time & date" button, and assuming your local time is good, click it. The page will refresh and the "System (Arduino) Date" and Time will update with the correct time. If not, refresh the page (F5).

13. Return to the home (main) page. The last image should be visible (unless the camera's capturing in Raw mode) and the camera's stats should show. If the camera's asleep, you'll be prompted to "Wake the camera", after which the page should update to show to camera, lens, image and battery information. If not, check:
   * the camera's USB cable is plugged in to the correct port on the Pi. It needs to be in the micro-USB port closest to the HDMI socket.

14. With the previous steps confirming active communication with the Arduino and camera, visit the Camera Settings (/Camera) page to confirm the setup and shoot a preview picture, and maybe name the board back on /System.

15. Visit the Intervalometer page to set a test shooting schedule. Select at least the current day and a relatively frequent interval (e.g. 5 minutes). Back on the home page, the "Next shot:" day and time should now show correctly. Confirm the photo is taken at the nominated time, and that the Last shot and Next shot values update as expected.

16. If you're preparing the board for deployment, reset the settings on the /intervalometer page to their final values.

17. On the /System page, set whether the Pi is to be permanently powered ("Always On" is at the top of the "Pi on at (hour):" scrolling list) or at what time each day it will perform its daily sync with the camera and be available for maintenance review, and for how long. Choose an appropriate duration, making sure you allow sufficient time for an entire day's photos to transfer to the Pi.

18. If you're NOT planning to leave the Pi permanently on, wait for the "Pi on for (minutes):" duration to elapse. The HDMI monitor will capture the Pi's shutdown and most likely go into sleep mode, and the PCB's LED will extingish as it returns to sleep.

19. If you now press / activate the Reed switch, the LED will flash three times and remain light to indicate the Arduino is awake, and your action will again cause the Arduino to wake the Pi. As long as the Pi is awake, the Arduino will remain awake, so with the MC jumper present, the LED will remain on.

20. Once you're finished with your testing:
   * remove the MC jumper.
   * wait for the Pi to go to sleep, then remove power from the PCB. 
   * If you've set the Pi to be "Always On", or want to send it off to sleep without waiting, you can shut it down by either:
      * ssh-ing to it and initiating the shutdown command `sudo shutdown now`, or 
      * remove the jumper that's on the top two pins of J2.
   * Once the Pi has shutdown, remove power from the board and reinstate the top J2 jumper.

Happy time-lapsing!!

<br>
<hr >


## Further Reading

- [Advanced config options](/docs/advancedConfig.md)
- [Troubleshooting](/docs/troubleshooting.md)

