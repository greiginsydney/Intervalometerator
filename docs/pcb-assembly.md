# PCB Assembly

The PCB provided for the intvlm8r is a compact double-sided board with a screen-printed component overlay.

All components are commonly-available through-hole devices. As described, PCB-mounting sockets have been used for all the off-board connections, however these are of course optional and removing them will reduce the component cost.

Test points and jumpers have been added around the board to make assembly, testing and debugging as easy as possible. The use of these is described in this document, and in the troubleshooting pages on the project's wiki.

## Tools

To assemble the board you'll require:
* a soldering iron, solder & solder wick
* a multimeter, capable of reading DC volts and measuring continuity
* a drill and bit/s (if mounting work is required - see 'Before you Start')
* wire cutters and pliers (for bending & cutting component legs, etc)
* a 12V DC power supply (for testing)
* your camera & remote control cable (again, for testing)
* contact epoxy (only needed if your 2.5mm camera socket isn't pin-compatible with the PCB)

## Before you Start

1. Before you start, give the board a good visual check. Look for any places where solder may have bridged adjacent pads. We've deliberately kept the board as spaced out as possible, so the risk of this should be negligible.

2. Check the mounting holes are the right size for your intended case or housing. If you plan to mount the PCB directly to another piece of material, use the board now as a drilling template.

## Prep the Arduino

The Arduino requires some attention before we get too involved with the build. We need to remove a tiny solder link, remove the LED, and then add some short leads for the I2C bus connections, as those aren't brought out on the standard DIP28 package pins. The next three steps take you through the process.

3. To minimise power consumption we're not using the on-board voltage regulator. On the SparkFun Pro Mini this is easily achieved by removing the solder joining the two pads as shown here, just below the pin labelled GND on the top edge. (Here's where you'll want that fine solder wick.) If you're using another manufacturer's version of the Pro Mini, check the datasheet for your options here, which may require you to remove the regulator altogether.

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/56710964-f456c680-676b-11e9-9d85-5478c28bdfbd.png" width="50%">
 </p>

4. Solder two short flying leads to the pins marked SDA and SCL. These will connect to J3. There doesn't seem to be an agreed global colour-code for I2C, so I've adopted the seemingly common-place blue and yellow, with SDA = Blue and SCL = Yellow. (I remind myself of this by saying "SCYellow".)

5. The green LED near the reset button (still present in the bottom left corner of the image above) is connected to IO pin 10, which is also used by the SPI interface to the RTC, so to conserve power it has to go. Locking pliers or tweezers will help you get a grip on it while you desolder each leg, but of course if you mangle it in the process that's OK, as it's going in the bin regardless. Just make sure you get it all and don't leave any leftovers still on the board, risking making electrical contact with anything nearby.

6. That's it for now. Set the Arduino to one side and continue with the PCB.


## Adding the Components

7. The first thing to add to the board is the PCB-mount 2.5mm socket that connects to the camera's remote control. The board has been laid out for 4 common styles, including those on offer from Farnell/Element14 and Amazon. Gently push the socket through the holes. Its body should be square with the board and the face should align with the front of the board, or protrude slightly. If it's not square you might have it in the wrong holes, or it's not one we've catered for.

8. Before soldering it into place, confirm that the three pins route to the 3 adjacent test points labelled "SLV", "TP1" and "TP2". Note that there are tracks on both sides of the board, so it might be a challenge to confirm. If all looks OK, solder the socket to the board.

> If your socket isn't pin-compatible with the board, use some contact epoxy to glue it on top of the component overlay and run short wires from the pins to SLV, TP1 and TP2, where SLV is the common ('sleeve') and TP1 and TP2 are Tip(T) and Ring(R). It doesn't matter which one T & R go to, as we'll test and correct for them next.

9. Because the pinouts differ between sockets, you need to confirm the Wake and Fire pins are the right way 'round. Plug the camera in to the board via the remote control cable.

10. After making sure the camera is turned on but asleep, tap a small piece of wire or a jumper lead to briefly join test points "SLV" and "TP1" - about half a second should be plenty of time. If this wakes the camera, you will need to add some short pieces of wire to the links in position "A" at J3 and J4. If the camera took a photo then you need position "B". If the camera's still asleep, tap the same wire between "SLV" and "TP2". This should have woken it, and indicates you need to use position "B" below. 

> If neither test woke the camera, check first the camera cable, then double-check the socket and your soldering. Disconnect the camera first then use your multimeter to confirm the T, R & S pins all appear on the test points, and that there are no short circuits between them.

> Picture goes here - TP jumper wires

11. Note these two links MUST be installed diagonally, so position "A" requires you to link the bottom two pins on the left-hand side and the upper two pins on the right. These settings should never need to change, but you may choose to use 3-pin header connectors here if you like.

> Picture goes here - Wake/Fire headers

12. With the camera working correctly, add the rest of the passive components, starting with the resistors, then the capacitors and the 2, 3 and 4-way headers. Take care that you solder the 47uF capacitor with its negative lead on the left, and that you don't mix up the two 100nF capacitors. The brown ceramic capacitor is between the Arduino and the RTC, whilst the polyester is below the 47uF electrolytic.

> There are three PCB pads for the ceramic capacitor to cater for components with either a 0.1" or 0.2" pin spacing without needing to bend the leads. If yours has the wider spacing, use the outer two pins, and if it's the smaller size, use the _lower_ two.

13. If you're using sockets for the Arduino or RTC, add those next, then the LED, the opto-couplers and finally the Maintenance Connector (MC), reed, power and camera sockets along the top edge. Be careful to note that the LED and optos are polarised. The LED has its flat (chamfered) side facing to the right, while the optos have their notch pointing up.

14. With your multimeter set to measure continuity, place the negative lead on the "0v" test point and then check the neighbouring power rail test pins. Your meter might beep or indicate briefly when touched to the 12V rail as the 47uF capacitor charges, but otherwise there should be no continuity between any of the rails. If the meter reports any continuity, re-check your soldering, and don't continue until any issues are resolved.

15. If you're confident in your soldering and assembly skills, add all three voltage regulators next, but if you're not, just start with the 7.5V camera one at the far right. Apply a 12V DC supply to the battery input, taking care to get the correct polarity. Your multimeter should read 12V on the input and 7.5V on the camera connector.

16. Remove power before continuing.

17. Add the 5V and 3.3V regulators if you haven't already done so, taking care not to mix them up, as they're hard to tell apart. Re-apply power and confirm the expected voltages are at the corresponding voltage test points.

> If the 5V rail is dead, check you don't have a jumper on the top two pins of J1, as that's a debug/test setting that forces the 5V supply off. Removing the jumper will cause the supply to start, as will placing it on the lower two pins.

18. Remove power when you're done.

## Add the expensive bits

Now the board's essentially complete and the supply rails tested, it's time to add the expensive bits. 

19. Solder a flat/straight-through 7-way header to the RTC module, with the battery side up and pins down. (If in doubt, check the photos). If you'll be socketing this, remember to solder the short pins facing up through the RTC board, leaving the longer pins to mate with the socket.

20. Carefully insert the coin battery. Its positive side (the wider side) is facing up towards you. It may require some pressure, but don't go overboard.

21. If you're socketing the RTC, its socket should already be in place, so just plug it in. If you're not going with the socket, solder the RTC to the board now, but BE CAREFUL as it's powered. Shorting the adjoining GND and VCC pins while soldering might turn out to be a $30 mistake. (Voice of experience speaking).

22. Follow a similar process for the Arduino. Solder a 6-way 90-degree header to the top edge (which you'll use for programming) and then a flat/straight-through 14-way header to each side. I normally 'plug' the Arduino into a piece of veroboard or perfboard to help make sure the pins are properly aligned while I solder them - or the PCB itself can be used for this.

> If you're not socketing the Arduino, there's the potential risk that the programming header pins will foul the track underneath. If that's the case, either trim them carefully, or consider mounting the header *underneath* the board.

23. If you're socketing the Arduino, its socket should already be in place, so just plug it in. 

24. If you're not going with a socket, solder the Arduino in position. Take care that the underside of the programming header pins and the SDA/SCL leads don't foul any of the tracks underneath.

25. Plug or solder the SDA and SCL flying leads to the marked pads underneath J2.

26. Mount the Raspberry Pi to the board using 2.5mm screws and spacers. I used 6mm-long bolts and threaded spacers from Farnell, but 1"/25mm long bolts and unthreaded spacers will do the job just as well - just make sure the bolt heads aren't encroaching on any of the neighbouring tracks. (In this case I suggest the bolt head should be on the top of the Pi with the washer and nut underneath the PCB.)

27. With the Pi firmly mounted on the board, thread 9 small lengths of tinned copper wire through the mating holes to the pads underneath. Solder them all on the top-side of the Pi, then flip the board over and solder the underneath.

28. You're done!

## Ready for Testing

29. If you've programmed the Pi, place a link on the top two pins of J1. This will keep the 5V supply off and the Pi powered down. We don't want it running just yet, as each time you apply and remove power without following a proper shutdown procedure risks corrupting its drive.

30. Re-apply the 12V DC power.

31. If you've already programmed the Arduino, the LED on the PCB's top edge will flash 8 times to indicate this is a first-time power-up (or power-up with a dead RTC battery), and no alarms have been set. The Arduino will set its clock to midday on January 1st, 2019 and commence an emergency backup program, firing a shoto every 15 minutes until someone - you - sets the clock. If not, the LED should remain off.

32. Again re-check the 3.3V and 7.5V supply rails are as expected, and that the 5V line reads 0V. Re-check your wiring and soldering if any of those aren't as expected.

33. Remove the power and continue with [Bench Testing](docs/bench-testing.md) when you're ready.


