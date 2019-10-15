# Advanced Config

The PCB was designed to permit a range of operating modes, primarily intended to make code development and bench testing a little easier.

These modes focus on jumpers J1 and J2.

## J1 - Pi power
J1 controls the Enable line to the 5V (Raspberry Pi) power supply:
- With the upper 2 pins jumpered, the 5V supply is forced off. In this position you're free to work on the Arduino or the rest of the board without needing to be concerned for the Pi. You should only move the jumper TO this position once the Pi has been shutdown, or while the board is without power, otherwise you risk drive corruption.
- With the lower 2 pins jumpered, the 5V supply/Pi will be powered under the control of the Arduino. This is the normal mode of operation. You should only move the jumper TO this position once the Pi has been shutdown, or while the board is without power, otherwise you risk drive corruption.
- With NO pins jumpered, the 5V supply will always operate, and the Arduino will not be able to de-power the Pi - although depending on J2 the Arduino may still be able to put the Pi to sleep.

## J2 - Controller interop
J2 - a 4-way jumper - links (or breaks) the control interfacing between the Arduino and the Pi.

**Normal Operation** has all 4 pins jumpered: the top two have a jumper and the bottom two also have a jumper. In this mode, the 'Shutdown' signal from the Arduino is presented to the Pi, and the 'Pi Running' signal returns to the Arduino. 

**No Pi mode**. If you want to isolate the Pi and the Arduino, remove both jumpers and link the _centre_ two pins. This applies a 'loopback' to the Arduino, fooling it into thinking there's a very responsive and compliant Pi on the other end. In this mode, as soon as the Arduino drops the 'Shutdown' line (pin 9), its pin 8 sees the 'Pi Running' line drop, confirming the Pi has gone to sleep and its power can be safely removed, which the Arduino then does via pin 7 and J1.

## Manual Pi Shutdown

If you're working on the bench there are two ways to initiate an elegant shutdown of the Pi. The first is to ssh to it and initiate the command `sudo shutdown now`. The second is to remove the jumper that's on the top two pins of J2. This is an active-low signal to the Pi, and it has an internal pull-up resistor. If you have a logic probe or voltmeter, you will see the bottom pin of J2 (IO 17 on the Pi) will drop from logic 1 (3.3V) to 0v when the Pi has entered sleep. Don't reinstate this jumper until you've removed power from the board, or moved J1 to the top two pins.