# Shopping List

All components were sourced in Sydney, Australia through 2018 & 2019. We won't anticipate you'll have any problems sourcing these items.

| Section | Approx pricing |
| :--- | ---: |
| [Photographic](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#photographic) | $ |
| [Electronics](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#electronics) | $ |
| [Hardware](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#hardware) | $ |
| __TOTAL__ | $ |

<br>

## Photographic
#### A camera (Canon 60D)
See the [Design Decisions](https://github.com/greiginsydney/Intervalometerator/wiki/Design-Decisions#why-i-chose-the-60d) page on the project's Wiki for the logic behind specifying this.

- [eBay](https://www.ebay.com/bhp/canon-60d)
    
    $AUD400

#### 18-55mm EF-S Lens

See the [Design Decisions](https://github.com/greiginsydney/Intervalometerator/wiki/Design-Decisions#why-i-chose-the-60d) page on the project's Wiki for the logic behind specifying this.

- [eBay](https://www.ebay.com/sch/i.html?_nkw=18-55mm+EF-S)
    
    $AUD75

#### DC  Power Coupler to suit

Aka a "fake battery". We cut off the USB plugs, stripped the cable and terminated it directly to the matching plug for the PCB-mounted socket. If your camera has an auxiliary power input this coupler won't be necessary - substitute a suitable plug and cable instead.

- [eBay](https://www.ebay.com/itm/Power-bank-usb-for-Canon-EOS-5D-7D-Mark-II-6D-80D-camera-DR-E6-dc-coupler-LP-E6/123101336453?hash=item1ca9695385:g:dWAAAOSwsQFa4ZVV:rk:1:pf:0)
    
    $USD25, ~$AUD35

#### Shutter Release cable to suit

- [PhotoShopStudio (AU)](https://www.photo-shop-studio.com.au/remote-control-trigger/cable-release/jjc-shutter-release-cable-a-canon-rs-80n3/)
    
    $10

#### Manfrotto Rapid Connect Adapter with 357PLV Camera Plate

- [John Barry Group (AU)](https://secure.johnbarry.com.au/manfrotto-357-sliding-plate-mav-357)
- [Amazon]()
- [B&H](https://www.bhphotovideo.com/c/product/554151-REG/Manfrotto_357_357_Pro_Quick_Release.html)

    ~$AUD83
    ~$USD60

#### 77-82mm filter step-up ring

- [PhotoShopStudio (AU)](https://www.photo-shop-studio.com.au/filters-step-rings/step-ring/fotolux-step-up-ring-77-82mm/)
- [Amazon]()

    $10	

#### 82mm UV or ND filter

- [PhotoShopStudio (AU)](https://www.photo-shop-studio.com.au/search.php?search_query=Hoya+82mm+filter)
- [Amazon]()
    
    $50 - $100

#### Right-Angle Mini-B USB cable

This one's optional, and depends on your choice of housing and camera. We wanted a right-angle USB plug to come out of the camera. This one ended in a Male A, necessitating the use of the second USB cable (see Electronics/ Pi).

- [eBay](https://www.ebay.com.au/itm/112701227087)

    $AUD2


### SUBTOTAL: $582

## Power

#### 12V Sealed Lead-Acid Battery
Careful with this one. The 12V 2.2Ah SLA battery we went with only *just* fits inside the Pelican case.

- [Jaycar Electronics (AU)](https://www.jaycar.com.au/12v-2-2ah-sla-battery/p/SB2482)
    
    $AUD24

#### 12V Solar Charger

12V 6A Battery Charging Regulator for Solar Panels

- [Jaycar Electronics (AU)](https://www.jaycar.com.au/12v-6a-battery-charging-regulator-for-solar-panels/p/AA0348)

    $AUD30

#### 20 watt solar panel

12V 20W MONO SOLAR PANEL TRICKLE POWER CHARGER RV AGM Complete Kit 4WD 4x4

- [eBay](https://www.ebay.com.au/itm/112750149497)
    
    $AUD49


#### Cable entry gland

You only need two holes in the box - one to let the light in, and another for the power. For the power input, you'll need some sort of gland to provide a water-tight seal.

You should be able to source these from your nearest electrical wholesaler, hobbyist electronics shop, or maybe a marine supplies shop (if you're near water).

- [Cabac (AU)](https://www.cabac.com.au/product-specs/13450510/GN12S)

    $AUD2 (?)

#### Miscellaneous

Your choice of solar panel might require some bracing or a bracket in order for it to mount to a pole. For ours we used two lengths of some 2" aluminium angle that we had to hand, resulting in a U-shaped support.

    $AUD ??

### SUBTOTAL: $103


##  Electronics
#### Arduino Pro Mini 328 

I went with the 3.3V 8MHz model for its minimal current consumption and pin-compatibility with the Pi's 3.3V IO pins. You *will* get better performance out of the 5V version, but also inherit an obligation to add a level converter for the pins (not described here). 

- [SparkFun](https://www.sparkfun.com/products/11114)
- [Amazon](https://amzn.to/2JAzSue)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1993-Arduino-Pro-Mini-328-3-3V-8MHz)

    $AUD16

#### FTDI programming cable

Don't be tempted to go with a generic 5V programming cable - stick with a 3.3V version to match the Arduino, otherwise your in-situ programming will result in the Arduino presenting 5V into the 3.3V pins of the Pi.

- [SparkFun](https://www.sparkfun.com/products/9873)
- [Amazon](https://amzn.to/2YsdbfV)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1615-SparkFun-FTDI-Basic-Breakout-3-3V)

    $AUD25

#### Raspberry Pi Zero W

I went for the Pi Zero as it met my needs for a low-current, low-cost unit in a small footprint - and less than half the cost of the larger models. There's nothing stopping you upgrading to a Model 2 or 3, but be aware that some of the config options will be slightly different.

- [Amazon](https://amzn.to/2HcmVVA)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/5288-Raspberry-Pi-Zero-W)

    $AUD25

#### USB "OTG" cable

You will recognise this as a micro-USB plug to a USB-A socket, but it's officially known as an On-The-Go (OTG) cable. Your Pi supplier probably offers these as an option with the Pi, so you can connect "standard" USB peripherals to the Pi. It's only required in the finished unit if you can't source a single USB cable to run from the camera to the Pi.

- [Amazon](https://amzn.to/2Hf45gI)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/5287-USB-OTG-Cable-Female-A-to-Micro-B-5in)
- [Core Electronics (AU)](https://core-electronics.com.au/micro-usb-otg-host-cable-for-raspberry-pi-zero.html)

    $AUD5

#### Mini HDMI cable/adapter

As with the OTG cable, your Pi supplier will surely offer these with the Pi, as you'll need it to connect your desktop monitor for the initial config steps.

- [Amazon](https://amzn.to/2JH5oH1)
- [Robot Gear (AU) - cable](https://www.robotgear.com.au/Product.aspx/Details/5285-Mini-HDMI-Cable-3ft)
- [Core Electronics (AU) - adapter](https://core-electronics.com.au/mini-hdmi-to-standard-hdmi-jack-adapter-for-raspberry-pi-zero.html)

    $AUD8


#### SanDisk 128GB Ultra Micro SDXC Memory Card

Choosing a larger size allows you to maximise the off-camera storage in the Pi. Be careful though, as once you go over 32G you're beyond the capabilities of the FAT file system and you're at greater risk of finding the Pi won't read the card. I used ["RPi SD cards"](https://elinux.org/RPi_SD_cards) as a helpful reference to find the card we went with here.

- [Amazon](https://amzn.to/2VtwU1D)
- [Officeworks (AU)](https://wwhttps://www.officeworks.com.au/shop/officeworks/p/sandisk-128gb-ultra-micro-sdxc-memory-card-sdsq128gb)

    $AUD50


#### Real-Time Clock
DeadOn RTC Breakout - DS3234

- [Amazon](https://amzn.to/2YnBGup)
- [SparkFun](https://www.sparkfun.com/products/10160)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1693-SparkFun-DeadOn-RTC-Breakout-DS3234)

    $AUD24

#### Coin-cell Backup Battery

The DeadOn RTC requires a 3V lithium backup battery. The common CR1225 or the slightly thinner CR1220 are compatible here. Your DeadOn supplier will probably have these in stock, otherwise they're the sort of item you might get from the local electronics hobby store or key-cutting kiosk.

- [Amazon](https://amzn.to/2JzfRUC)
- [Jaycar Electronics (AU)](https://www.jaycar.com.au/cr1220-3v-lithium-battery/p/SB2527)

    $AUD3

#### 3.3V regulator (Arduino)

Pololu 3.3V, 500mA Step-Down Voltage Regulator D24V5F3

- [Pololu](https://www.pololu.com/product/2842)
- [Amazon](https://amzn.to/2E2tHeB)
- [Core Electronics (AU)](https://core-electronics.com.au/pololu-3-3v-500ma-step-down-voltage-regulator-d24v5f3.html)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1017-3-3V-500mA-Pololu-Step-Down-Voltage-Regulator-D24V5F3)

    $AUD7


#### 5.0V regulator (Raspberry Pi)

Pololu 5V, 500mA Step-Down Voltage Regulator D24V5F5

- [Pololu](https://www.pololu.com/product/2843)
- [Amazon](https://amzn.to/2Jy7SY1)
- [Core Electronics (AU)](https://core-electronics.com.au/pololu-5v-500ma-step-down-voltage-regulator-d24v5f5.html)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1018-5V-500mA-Pololu-Step-Down-Voltage-Regulator-D24V5F5)

    $AUD7

#### 7.5V regulator (Camera)

Pololu 7.5V, 2.4A Step-Down Voltage Regulator D24V22F7

- [Pololu](https://www.pololu.com/product/2860)
- (not available on Amazon)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1007-7-5V-2-4A-Pololu-Step-Down-Voltage-Regulator-D24V22F7)

    $AUD13

#### Opto-Isolators

I went with bog-standard Motorola 4N25 6-pin DIP opto-isolators. These (or an equivalent) should be easy enough to find anywhere.

- [Amazon](https://amzn.to/2E31nJk) (Pack of 10)
- [Element 14](https://au.element14.com/vishay/4n25/optocoupler-transistor-5300vrms/dp/1612453?st=4n25)

    $AUD1 (each - you need two)

#### Concealed Timber Door Frame Reed Switch
So as to save opening the case when its in situ, we added a standard door reed switch you might find used in a burglar alarm. Wave a magnet on the outside of the box, and in the configuration presented here it will wake the Raspberry Pi for the previously-set "WakeTime" duration. (Again, this presumes a low-power setup with the Pi normally turned off).

- [Jaycar (AU)](https://www.jaycar.com.au/concealed-timber-door-frame-reed-switch/p/LA5075)

    $AUD5


#### 2.5mm stereo socket

This is to connect the intervalm8r to the camera's shutter cable. The PCB has been designed to accommodate all the thru-hole PCB-mounted sockets we could buy online. You could just as easily choose in-line instead, or a directly-connected cable. Change this to a suitable connector if your camera shutter release cable uses a different type. (See ["adding the components"](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step4-pcb-assembly.md#adding-the-components) in the PCB assembly.md for more details and options.)

- [Element 14]()
- [Amazon]()

#### 3mm Green LED (optional)

As the project is presented, this LED lights when the Arduino is awake, but only if the adjacent jumper is connected (taking Arduino input A0 to ground). I used it as a generic headless debugging aid. You should be able to find this just about anywhere: your Arduino/Pi supplier, local electronics hobby store, etc.

    $AUD1

#### Custom PCB

The custom PCB for the project is available on eBay.

- [eBay]()

    $AUD25.00, + shipping

#### Veroboard (alternative PCB)

An alternative to the PCB will be to build the board on Veroboard, aka stripboard. (There's an image of the Veroboard prototype on the [Wiki / history](https://github.com/greiginsydney/Intervalometerator/wiki/History) page.)   

- [Jaycar (AU)](https://www.jaycar.com.au/pc-boards-vero-type-strip-95mm-x-75mm/p/HP9540)

    $AUD4.50

#### Resistors

Resistors are used on the board for two purposes. They're either current-limiting the supply to the LEDs (the green one and the 2 optos) or providing pull-up or pull-down assistance to the IO pins. You should be able to find these just about anywhere: your Arduino/Pi supplier, local electronics hobby store, etc.
* Green LED: 1 x 150R 1/4W
* Optos: 2 x 150R 1/4W
* Arduino pin A8: 1 x 4.7k 1/4W
* Arduino pin A2: 1 x 4.7k 1/4W

    $AUD1

#### 47uF electrolytic capacitor

Every supply needs some smoothing. Optional but recommended.

- [Element 14](https://au.element14.com/multicomp/mcrh35v476m6-3x11/cap-47-f-35v-20/dp/9451935?rpsku=rel3:667894&isexcsku=false)

    $AUD0.30
    
#### 100nF polyester capacitor

Every supply needs a 100nF poly smoothing capacitor. Optional but recommended.

- [Element 14](https://au.element14.com/epcos/b32529c0104k000/cap-0-1-f-63v-10-pet-potted/dp/9750878?st=0.1%20uF%20polyester)

    $AUD0.30
    
#### 100nF ceramic capacitor

I really love the DeadOn RTC, however SparkFun appear to have omitted the chip manufacturer's recommended power supply capacitor. I went with a 100pF ceramic.

- [Element 14](https://au.element14.com/vishay/d101k20y5ph63l6r/ceramic-capacitor-100pf-100v-y5p/dp/1606155?st=100pf%20ceramic) (MOQ = 5)

    $AUD0.30


#### Miscellaneous

Header pins

Jumpers
- [Element 14](https://au.element14.com/multicomp/spc19807/mini-jumper-2-position-2-54mm/dp/1192775) (Pack of 25)

2.0mm Bolts (Raspberry Pi)
- [Element 14](https://au.element14.com/tr-fastenings/m2-6-prstmc-z100/screw-pozi-pan-steel-bzp-m2x6/dp/1420386) (Pack of 100)

2.0mm threaded spacers
- [Element 14](https://au.element14.com/ettinger/05-01-103/standoff-hex-female-brass-10mm/dp/2494574) (MOQ = 10)

Backmount (for mounting the PCB to)

3.0mm bolts (PCB to backmount)

3.0mm (dia) spacers

interconnecting wires.

    $AUD10 (Approx)

### SUBTOTAL: $201.80

## Hardware - casing and mounts

#### Pelican 1300 case

    $95

#### CCTV Camera Mount

    $AUD15

#### Ram Mounts

If your budget allows for it, check out some of the mounting options in the Ram Mounts range. Their ["C Size" mounts](https://www.rammount.com/search?query=c+size) will take up to a 5kg (~10lb) load.



## SUBTOTAL: $195

<br/>

### Declaration:
The Amazon links above are affiliate links. We may earn a small commission from purchases, however you pay no more for this.
