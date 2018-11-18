

## Electronics - Hardware
* [Overview](#overview)
* [Arduino](#arduino)
* [Raspberry Pi](#raspberry-pi)
* [SparkFun DeadOn RTC](#sparkfun-deadon-rtc)
* [Power](#power)

## Software
* [I2C](#i2c)
* [DeadOn Alarm 1](#deadon-alarm-1)
* [Python / Flask / Gunicorn](#python-flask-gunicorn)

## Camera
* [Why I chose the 60D](#why-i-chose-the-60d)
* [Lens](#lens)


<br><hr>

# Electronics - hardware

## Overview

This project started with just a Raspberry Pi doing the lot. That was the obvious choice given it runs Python, the target platform of Jim's python-gphoto2 project, from which this all stemmed.

It however became apparent early on in the piece that I couldn't use just one micro. The Pi family are all just TOO power-hungry on their own, and a little fragile as well. Every time you turn a Pi off inelegantly (it's gonna happen) you risk drive corruption and a dead intvlm8r. So that resulted in the Arduino being added into the mix.


## Arduino 

With low-power mods and the ability to maintain deep sleep and consume micro-Amps while doing so, the <a href="https://www.sparkfun.com/products/11114" target="_blank">Arduino Pro Mini</a> is the master controller.

I chose the 3.3V Pro Mini for two reasons:
* it has lower power consumption than the 5V version.
* having its IO pins running at 3.3V meant I could directly connect to the IO pins on the Pi (which also run at 3.3V, despite being fed by 5V in) without needing voltage converters. (Yes, I'm taking a purist's approach here. There appears to be plenty of evidence on the Internet that you can connect them together.)

Going with the 3.3V pro mini meant some compromises on speed and performance, but these only manifest - and then only intermittently - when you're talking to it via the I2C bus from the Pi.

## Raspberry Pi

The initial prototype was constructed around a Model B I had on hand, but after some research I settled on the <a href="https://www.raspberrypi.org/products/raspberry-pi-zero-w/" target="_blank">Pi Zero W</a>. I liked its on-board WiFi (albeit only 2.4GHz) and relatively low power consumption. Its small size helped too, enabling me to build the lot onto a piece of Veroboard / strip-board.

In a low-current setup the Pi lies dormant, only woken once a day by the Arduino for a short period. On bootup the Pi copies any new photos from the camera to its on-board memory card, whilst its web-server is active should anyone want to query it or check/change any settings in the Arduino or camera. 

Critically, out in the field the Pi could die totally and the Arduino will still keep firing photos.

## SparkFun DeadOn RTC

Whilst not without its shortcomings, I love the <a href="https://www.sparkfun.com/products/10160" target="_blank">SparkFun DeadOn RTC</a>. It's probably the first one I found, and nothing I've seen of its contemporaries has given me cause to jump ship.

It runs on a range of voltages, has 2 completely *independent* alarms, is battery-backed, and has an output pin that you can set to go low when an alarm fires. It's this pin that connects to the hardware interrupt pin on the Arduino to wake it from sleep.

## Power
The project initially started out based on 2 x LiIon 18650 batteries and a controller from eBay. At full charge, two of these in series generate 8.4V, just what the Canon wants to see. The voltage regulators then provided the always-on 3.3V supply for the Arduino and RTC, and the separate 5V rail (under Arduino control) to run the Pi.

Things didn't go well. The controller died not long into testing phase, and we found the ONLY place on the planet we could source a 7.4V charge controller was the same eBay merchant, and it would take another month to get here from China.

That prompted a re-think, and at about the same time our friend Amfony explained that relying on 2 series 18650's without direct per-cell charging was a recipe for disaster. One of the two cells would eventually weather and die, going open-circuit to protect itself from making like a flare, and in so doing kill the whole intvlm8r.

And so we changed back to a bog-standard SLA battery and 12V charger, introducing a third VReg, this one to supply 7.5V to the camera.

Why 7.5V? Having learnt the lesson about using hard-to-find components, we found Pololu make a 7.5V version that's well-stocked here in Australia, and thus presumably everywhere else too. Running the camera on 7.5V - whilst it reports its "battery" is only at 50% capacity - means we can discharge the 12V SLA battery down to ~8V before the VReg will die and we'll stop taking photos. (Hopefully it will never come to that of course!)

<br><hr>
# Software

I wanted to document why a few of the decisions were made in the software.

## I2C
There are many posts about how to interconnect a Pi and an Arduino.

A key point to note is that the Pi **must** be the Master, so only it can initiate contact. For the bulk of what we're doing that's not a problem. 

I struggled with the interface, but found <a href="https://www.slideshare.net/MikeOchtman/i2c-interfacing-raspberry-pi-to-arduino" target="_blank">this article</a> was a godsend. Thank you Mike Ochtman.

You'll see in the build steps that I've deliberately wound back the speed of the I2C interface to 40kHz, and this is purely to give the poor little 8MHz Arduino time to breathe. This is also why in some of the Python pages I send multiple requests to the Arduino with a delay between them, rather than consolidate them. (e.g., I query the date and then the time separately in both main & system).

FYI, the Pi Zero W *does* apparently have pullup resistors on the SDA & SCL pins, even though they're <a href="https://www.raspberrypi.org/documentation/hardware/raspberrypi/schematics/rpi_SCH_ZeroW_1p1_reduced.pdf" target="_blank">not shown on the published circuit</a> (v1.1 at the time of writing). (<a href="https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=224187" target="_blank">Forum thread on the subject</a>).

## DeadOn Alarm 1
In the development cycle I had the Arduino "SetAlarm1" function setting the alarm for the next time a photo was required, down to the day. So if we're shooting a Monday-to-Friday setup, after the last shot was taken on Friday the alarm was set for the first shot on Monday. The benefit being that the Arduino could remain in deep sleep until it was needed next.

I changed this in order to add a little more resilience to the intvlm8r.

As coded above, should for some reason the RTC / Arduino miss an alarm and forget to shoot - or more importantly forget to reset the alarm - the next time the alarm would fire would be a week from now, so we'd lose a week's construction.

The code now doesn't bake the day into the alarm, and so in the scenario above, after the last Friday shot the alarm will be reset to (say) 6am, where it will fire through the set hours on both Saturday and Sunday. Each time the alarm goes off it will wake the Arduino, the timer will be reset, however a photo won't be taken. The day test in loop() ensures it only shoots on the days configured.

As it is in this modified config, should the RTC / Arduino miss an alarm, you should only lose 24 hours of construction.


## Python Flask Gunicorn
I've never seen Python before in my life. I'm sure there's plenty of room for a skilled contributor to improve it vastly.
<br><hr>
# Camera
## Why I chose the 60D
* This is a Canon shop. 
* I’d already tested gphoto on my 6D and know it will work. I couldn’t be sure I’d have the same success with the other brands. I am probably be wrong on that.
* I chose a mirror over mirrorless so the sensor can’t suffer any burn in from being exposed to the same scene for months on end.
* Partly because I already had the DC Coupler for it and I knew that the 60D would use it.
* On eBay not much price difference between 60D and lesser models.
* 12MP wo
uld give me plenty of digital zoom if the final. 18MP allows me to have digital zoom if I end up going for 4K. 

A lesser model could be a better option because of size and weight.

Comparing 18MP models:


| Camera   | Weight   | Dimensions | Notes |
|----------|----------|------------|---|
| 60D | 755g |       145 × 106 × 79     |  |
|   600D       |    570g      |      133 × 100 × 80      |  |
|    1200D      |    480g      |     130 × 100 × 88       | (No coupler?) |
|    1100D      |     495g     |     130 × 100 × 78        | E10 Coupler works but it’s 12MP |


## Lens
* Canon 18-55mm f/3.5-5.6 IS is dirt cheap. Got one from eBay for next to nothing.
* Not sure of the framing so I wanted a wide to “normal” focal length.
* I don’t need Image Stabilisation. In fact, it must be turned off.
* Will probably use something like f/8 so don’t need a fast lens. May even use an ND filter.
* It’s not a fantastic lens, but should do the trick.
* My preference would be for a 24mm pancake lens if I could be sure of the shot.
