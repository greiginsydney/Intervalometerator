# Advanced Config

The PCB was designed to permit a range of operating modes, primarily intended to make code development and bench testing a little easier.

These modes focus on jumpers J1 and J2.

## J1 - Pi power
J1 controls the Enable line to the 5V (Raspberry Pi) power supply:
- With the upper 2 pins jumpered, the 5V supply is forced off. In this position you're free to work on the Arduino or the rest of the board without needing to be concerned for the Pi. You should only move the jumper TO this position once the Pi has been shutdown, or while the board is without power, otherwise you risk drive corruption.
- With the lower 2 pins jumpered, the 5V supply/Pi will be powered under the control of the Arduino. This is the normal mode of operation. You should only move the jumper TO this position once the Pi has been shutdown, or while the board is without power, otherwise you risk drive corruption.
- With NO pins jumpered, the 5V supply will always operate, and the Arduino will not be able to de-power the Pi - although depending on J2 the Arduino may still be able to put the Pi to sleep, from which it won't be woken until its power is toggled.

> If you have the Pi always powered (either by the above setting, or if you're separately powering an off-board Pi), set J2 to **No Pi mode** (described below) to prevent the Arduino from shutting it down.

## J2 - Controller interop
J2 - a 4-way jumper - links (or breaks) the control interfacing between the Arduino and the Pi.

**Normal Operation** has all 4 pins jumpered: the top two have a jumper and the bottom two also have a jumper. In this mode, the 'Shutdown' signal from the Arduino is presented to the Pi, and the 'Pi Running' signal returns to the Arduino. 

**No Pi mode**. If you want to isolate the Pi and the Arduino, remove both jumpers and link the _centre_ two pins. This applies a 'loopback' to the Arduino, fooling it into thinking there's a very responsive and compliant Pi on the other end. In this mode, as soon as the Arduino drops the 'Shutdown' line (pin 9), its pin 8 sees the 'Pi Running' line drop, confirming the Pi has gone to sleep and its power can be safely removed, which the Arduino then does via pin 7 and J1, before itself taking a nap until the alarm next fires.

## Manual Pi Shutdown

If you're working on the bench there are two ways to initiate an elegant shutdown of the Pi. The first is to ssh to it and initiate the command `sudo shutdown now`. The second is to remove the jumper that's on the top two pins of J2. This is an active-low signal to the Pi, and it has an internal pull-up resistor. If you have a logic probe or voltmeter, you will see the bottom pin of J2 (IO 17 on the Pi) will drop from logic 1 (3.3V) to 0v when the Pi has entered sleep. Don't reinstate this jumper until you've removed power from the board, or moved J1 to the top two pins.

## Other Pi Models

Whilst designed for low-power operation using the Pi Zero W, the intvlm8r has been tested with a number of Pi variants throughout its development lifecycle.

All modern Pis share the same IO pinouts, so substituting a Pi 2, 3 or later for the Zero is just a matter of making a wiring hardness to connect the Pi back to the board. A pair of 14-pin IDC header connectors would do the job nicely.

This image shows a 16-pin [Pololu 973](https://www.pololu.com/product/973) IDC ribbon connecting to a Pi 3B+:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/69041899-66626600-0a44-11ea-8b9a-315526221fb0.jpg" width="50%">
</p>

Using an IDC ribbon like this required me to sacrifice two IO pins on the Pi, but if you're planning on this being a permanent setup hopefully it won't be an issue for you:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/69042535-74fd4d00-0a45-11ea-8da7-4329ae21b513.jpg" width="50%">
</p>

The only other change is to swap out the 5V regulator for a higher current model. The [Pololu D24V10F5](https://www.pololu.com/product/2831) supplies up to 1A @ 5V, which [the internet suggests](https://www.pidramble.com/wiki/benchmarks/power-consumption) might _not_ quite be enough for the latest Pi models, so maybe consider [the 2.5A D24V22F5](https://www.pololu.com/product/2858) instead. At 0.7" x 0.7" it's a little larger than [the original 500mA version scoped](https://www.pololu.com/product/2843) (0.4" x 0.5"), but still pin-compatible.

Its extra height will foul J3 and its width the Wake opto-isolator, but some longer stand-off wires should add the necessary clearance for the opto. Consider replacing J3 with a link, or maybe install it on the under-side of the board. (The plated-through holes of the offered PCB mean you can solder either side.) I went for a small piece of insulation (stripped from some cable) to use as a spacer to raise the power supply up a little, and then added some hot glue just to make sure there was both separation and no risk of movement:

<p align="center">
<img src="https://user-images.githubusercontent.com/11004787/69042126-ca852a00-0a44-11ea-81d3-cfe360dd6e4c.jpg" width="50%">
</p>
<br>

> If you're separately powering an off-board Pi and it's set to always run, the 5V regulator & J1 can be omitted. In this config, set J2 to **No Pi mode** (described above) to prevent the Arduino from shutting it down.


