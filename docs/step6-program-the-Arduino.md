# Program the Arduino

Before you can program the Arduino you'll need to have the appropriate programming header on it, which is documented in the "[Prep the Arduino](/docs/step5-pcb-assembly.md#prep-the-arduino)" steps in [step5-pcb-assembly](/docs/step5-pcb-assembly.md). Please jump there now if you've not completed those steps already.

## Downloads

1. You'll need three downloads in order to program the Arduino. On top of the obvious need for the Arduino IDE, there are two external libraries that are essential:

- [Aduino IDE](https://www.arduino.cc/en/Main/Software). (I use the "Windows Installer, for Windows XP and up" version).
- [rocketscream Low-Power](https://github.com/rocketscream/Low-Power) library.
- [SparkFun DS3234 RTC Arduino Library](https://github.com/sparkfun/SparkFun_DS3234_RTC_Arduino_Library).

2. For the two GitHub links, download each library by clicking on "Clone or download", and then "Download ZIP":

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/71568904-fb19b280-2b1e-11ea-8223-ce418f0fd6d3.png" width="80%">
</p>

3. Install and run the Arduino IDE. All the following steps are performed within the Arduino IDE unless noted otherwise.

4. Click Sketch / Include Library / Add .ZIP Library and point it to one of the ZIP files you just downloaded. Repeat for the other library's ZIP file.

5. Click File / Open... to open the "sketch" (the intervalometer.ino file) that's part of this repo, or create a new one (File / New) and paste the content in. (Then don't forget to File / Save As...).

6. The IDE can't determine the type of Arduino board it is to program, and it's not something we can bake into the sketch - you have to set it manually in the IDE. First step is to tell it we're using an "Arduino Pro or Pro Mini". Click Tools / Board and then click to select the Pro Mini as shown here:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/71569333-73ce3e00-2b22-11ea-959e-e2e468ca234e.png" width="80%">
</p>

7. There are 3.3V and 5V variants of the Pro Mini, so we also need to tell it which we're using. As documented here, we're using the 3.3V version. Click Tools / Processor and click to select the "ATmega328P (3.3V, 8MHz)" as shown here:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/71569342-83e61d80-2b22-11ea-825e-1d04800c3a40.png" width="80%">
</p>

8. Getting the USB port right can be the hardest part of the programming effort. Plug the programmer onto the Arduino's header, making sure you get it the right way around. Most have "BLK" and "GRN" screen-printed on them to align with the same markings on the Arduino.

> The Arduino doesn't even need to be mounted to the intvlm8r's PCB for these steps - the programmer will power the board!

9. On a Windows PC, open "Device Manager". You can do this by right-clicking the Start button and selecting Device Manager from the menu that appears, or by pressing the Win-R key combination and typing devmgmt.msc. (Hopefully you have permissions to do this!).

10. Expand "Ports (COM & LPT)" as shown here:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/71569588-45516280-2b24-11ea-9a52-35daf7e19340.png" width="80%">
</p>

11. Take note of the COM ports shown, then plug your programmer in to a spare USB port. All going well, a new port will appear: the Arduino.

> I've highlighted what I know to be the Arduino, because I opened Device Manager *before* plugging the Arduino in, and COM4 appeared. Your COM port could be any number.

12. Assuming the above succeeds, return to the Arduino IDE and select the port you've just found. Click Tools / Port & click the correct one.

13. Now's the big test. Click Sketch / Upload, or type ^-U. The sketch will be compiled and then uploaded. Note the teal-coloured task bar immediately below the code will display "Compiling Sketch ...", then "Done compiling", and commence the upload, with "Uploading..." and then "Done uploading".

14. If you hit errors with the Compile step, one of the first steps to do is click Tools / Fix Encoding & Reload. Sometimes rogue text formatting sneaks in, and this step will cleanse that. Repeat step 13, and if it still fails, check for any obvious typos or indicators of the failure in the black text box at the bottom of the IDE. You can drag the top of the teal bar to enlarge or reduce this pane. 

15. If you've gone OK, unplug the programmer from the Arduino and the computer. Mission accomplished.


## Next Steps

- If you've not completed it already, return to [step5-pcb-assembly](/docs/step5-pcb-assembly.md).
- or otherwise jump to [step7-bench-testing](/docs/step7-bench-testing.md).
