# Shopping List

All components were sourced in Sydney, Australia through 2018 & 2019. We won't anticipate you'll have too many problems sourcing these items.

Notes:
- All pricing shown here is approximate, and excludes shipping costs.
- The totals reflect the unit price and don't take into account that some merchants require you to purchase more than 1.
- All Element 14 links should readily translate to Avnet and Farnell links for other markets. (They're the same company).


<br>

| Section | Approx pricing AU | Approx pricing USA |
| :--- | ---: | ---: |
| [Photographic](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#photographic) | $690 | $501 |
| [Electronics](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#electronics) | $213 | $160 |
| [Power](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#power) | $113 | $83 |
| [Hardware](https://github.com/greiginsydney/Intervalometerator/blob/master/SHOPPINGLIST.md#hardware) | $112 | $76 |
| __TOTAL__ | __$1128__ | __$820__ |

<br>

## Photographic
#### A camera (Canon 60D)
See the [Design Decisions](https://github.com/greiginsydney/Intervalometerator/wiki/Design-Decisions#why-i-chose-the-60d) page on the project's Wiki for the logic behind specifying this.

- [eBay (US)](https://www.ebay.com/b/Canon-EOS-60D-Body-Only-Digital-Cameras/31388/bn_105856154)
    
    ~ $AUD400</br>
    ~ $USD250
    

#### 18-55mm EF-S Lens

See the [Design Decisions](https://github.com/greiginsydney/Intervalometerator/wiki/Design-Decisions#why-i-chose-the-60d) page on the project's Wiki for the logic behind specifying this.

- [eBay](https://www.ebay.com/sch/i.html?_nkw=18-55mm+EF-S)
    
    ~ $AUD75</br>
    ~ $USD75

#### DC  Power Coupler to suit

Aka a "fake battery". We cut off the USB plugs, stripped the cable and terminated it directly to the matching plug for the PCB-mounted socket. If your camera has an auxiliary power input this coupler won't be necessary - substitute a suitable plug and cable instead.

- [eBay](https://www.ebay.com/itm/Power-bank-usb-for-Canon-EOS-5D-7D-Mark-II-6D-80D-camera-DR-E6-dc-coupler-LP-E6/123101336453?hash=item1ca9695385:g:dWAAAOSwsQFa4ZVV:rk:1:pf:0)
    
    $AUD35</br>
    $USD25

#### Shutter Release cable to suit

- [PhotoShopStudio (AU)](https://www.photo-shop-studio.com.au/remote-control-trigger/cable-release/jjc-shutter-release-cable-a-canon-rs-80n3/) - 6D
- [Amazon](https://amzn.to/2W4ewcT) - 6D
- [Amazon](https://amzn.to/2MCu18L) - 60D and many others
    
    $AUD10</br>
    $USD9

#### Manfrotto Rapid Connect Adapter with 357PLV Camera Plate

- [John Barry Group (AU)](https://secure.johnbarry.com.au/manfrotto-357-sliding-plate-mav-357)
- [Amazon](https://amzn.to/2JdWdwr) - slightly different product, only 2" travel
- [B&H (USA)](https://www.bhphotovideo.com/c/product/554151-REG/Manfrotto_357_357_Pro_Quick_Release.html)

    $AUD83</br>
    $USD60

#### 77-82mm filter step-up ring

- [PhotoShopStudio (AU)](https://www.photo-shop-studio.com.au/filters-step-rings/step-ring/fotolux-step-up-ring-77-82mm/)
- [Amazon](https://amzn.to/33OybQD)

    $AUD10</br>
    $USD5

#### 82mm UV or ND filter

- [PhotoShopStudio (AU)](https://www.photo-shop-studio.com.au/search.php?search_query=Hoya+82mm+filter)
- [Amazon](https://amzn.to/2N5BQTp) - UV
- [B&H (USA)](https://www.bhphotovideo.com/c/product/11995-REG/B_W_66045076_82mm_UV_Haze_010.html) - UV
    
    $AUD50 - 100</br>
    $USD50 - 110

#### Right-angle Mini-B USB cable

This one's optional, and depends on your choice of housing and camera. We wanted a right-angle USB plug to come out of the camera. This one ended in a Male A, necessitating the use of the second USB cable (see Electronics/Pi).

- [eBay](https://www.ebay.com.au/itm/112701227087)

    $AUD2</br>
    $AUD2


### SUBTOTAL: AUD$690 / $USD501


##  Electronics
#### Arduino Pro Mini 328 

We went with the 3.3V 8MHz model for its minimal current consumption and pin-compatibility with the Pi's 3.3V IO pins. You *will* get better performance out of the 5V version, but also inherit an obligation to add a level converter for the pins (not described here). 

- [SparkFun](https://www.sparkfun.com/products/11114)
- [Amazon](https://amzn.to/31EvcbU)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1993-Arduino-Pro-Mini-328-3-3V-8MHz)

    $AUD16</br>
    $USD13

#### FTDI programming cable

Don't be tempted to go with a generic 5V programming cable - stick with a 3.3V version to match the Arduino, otherwise your in-situ programming will result in the Arduino presenting 5V into the 3.3V pins of the Pi.

- [SparkFun](https://www.sparkfun.com/products/9873)
- [Amazon](https://amzn.to/31AYmsn)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1615-SparkFun-FTDI-Basic-Breakout-3-3V)

    $AUD25</br>
    $USD18

#### Raspberry Pi Zero W

I went for the Pi Zero as it met my needs for a low-current, low-cost unit in a small footprint - and less than half the cost of the larger models. There's nothing stopping you upgrading to a Model 2 or 3, but be aware that some of the config options will be slightly different.

- [Core Electronics (AU)](https://core-electronics.com.au/raspberry-pi-zero-w-wireless.html)
- [Amazon](https://amzn.to/2MCdHow)

    $AUD15</br>
    $USD22

#### USB "OTG" cable

You will recognise this as a micro-USB plug to a USB-A socket, but it's officially known as an On-The-Go (OTG) cable. Your Pi supplier probably offers these as an option with the Pi, so you can connect "standard" USB peripherals to the Pi. It's only required in the finished unit if you can't source a single USB cable to run from the camera to the Pi.

- [Amazon](https://amzn.to/2JdZmfE)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/5287-USB-OTG-Cable-Female-A-to-Micro-B-5in)
- [Core Electronics (AU)](https://core-electronics.com.au/micro-usb-otg-host-cable-for-raspberry-pi-zero.html)

    $AUD5</br>
    $USD5

#### Mini HDMI cable/adapter

As with the OTG cable, your Pi supplier will surely offer these with the Pi, as you'll need it to connect your desktop monitor for the initial config steps.

- [Amazon](https://amzn.to/2MzJ1UQ)
- [Robot Gear (AU) - cable](https://www.robotgear.com.au/Product.aspx/Details/5285-Mini-HDMI-Cable-3ft)
- [Core Electronics (AU) - adapter](https://core-electronics.com.au/mini-hdmi-to-standard-hdmi-jack-adapter-for-raspberry-pi-zero.html)

    $AUD8</br>
    $USD7


#### SanDisk 128GB Ultra Micro SDXC Memory Card

Choosing a larger size allows you to maximise the off-camera storage in the Pi. Be careful though, as once you go over 32G you're beyond the capabilities of the FAT file system and you're at greater risk of finding the Pi won't read the card. I used ["RPi SD cards"](https://elinux.org/RPi_SD_cards) as a helpful reference to find the card we went with here.

- [Officeworks (AU)](https://wwhttps://www.officeworks.com.au/shop/officeworks/p/sandisk-128gb-ultra-micro-sdxc-memory-card-sdsq128gb)
- [Amazon](https://amzn.to/35TxoQ9)

    $AUD50</br>
    $USD20


#### Real-Time Clock
DeadOn RTC Breakout - DS3234

- [SparkFun](https://www.sparkfun.com/products/10160)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1693-SparkFun-DeadOn-RTC-Breakout-DS3234)
- (not available on Amazon)

    $AUD24</br>
    $USD11

#### Coin-cell Backup Battery

The DeadOn RTC requires a 3V lithium backup battery. The common CR1225 or the slightly thinner CR1220 are compatible here. Your DeadOn supplier will probably have these in stock, otherwise they're the sort of item you might get from the local electronics hobby store or key-cutting kiosk.

- [Jaycar Electronics (AU)](https://www.jaycar.com.au/cr1220-3v-lithium-battery/p/SB2527)
- [Amazon](https://amzn.to/32FdVk4)

    $AUD3</br>
    $USD4

#### 3.3V regulator (Arduino)

Pololu 3.3V, 500mA Step-Down Voltage Regulator D24V5F3

- [Pololu](https://www.pololu.com/product/2842)
- [Amazon](https://amzn.to/2qsuDVF)
- [Core Electronics (AU)](https://core-electronics.com.au/pololu-3-3v-500ma-step-down-voltage-regulator-d24v5f3.html)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1017-3-3V-500mA-Pololu-Step-Down-Voltage-Regulator-D24V5F3)

    $AUD7</br>
    $USD9


#### 5.0V regulator (Raspberry Pi)

Pololu 5V, 500mA Step-Down Voltage Regulator D24V5F5

- [Pololu](https://www.pololu.com/product/2843)
- [Amazon](https://amzn.to/35VGJHf)
- [Core Electronics (AU)](https://core-electronics.com.au/pololu-5v-500ma-step-down-voltage-regulator-d24v5f5.html)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1018-5V-500mA-Pololu-Step-Down-Voltage-Regulator-D24V5F5)

    $AUD7</br>
    $USD9

#### 7.5V regulator (Camera)

Pololu 7.5V, 2.4A Step-Down Voltage Regulator D24V22F7

> This regulator is *purely* for the camera, so choose a different voltage here if required.

- [Pololu](https://www.pololu.com/product/2860)
- (not available on Amazon)
- [Robot Gear (AU)](https://www.robotgear.com.au/Product.aspx/Details/1007-7-5V-2-4A-Pololu-Step-Down-Voltage-Regulator-D24V22F7)

    $AUD13</br>
    $USD10

#### Opto-Isolators

We used bog-standard Motorola 4N25 6-pin DIP opto-isolators. These (or an equivalent) should be easy enough to find anywhere.

- [Amazon](https://amzn.to/2NffJdp) - pack of 10, $USD6
- [Element 14](https://au.element14.com/vishay/4n25/optocoupler-transistor-5300vrms/dp/1612453?st=4n25)

    $AUD1 (each - you need two)</br>
    $USD1 (each - you need two)

#### Concealed Timber Door Frame Reed Switch
So as to save opening the case when its in situ, we added a standard door reed switch you might find used in a burglar alarm. Wave a magnet on the outside of the box, and in the configuration presented here it will wake the Raspberry Pi for the previously-set "WakeTime" duration. (This presumes a low-power setup with the Pi normally turned off).

- [Jaycar (AU)](https://www.jaycar.com.au/concealed-timber-door-frame-reed-switch/p/LA5075)
- [Amazon](https://amzn.to/2P8VT5X) - pack of 2, $USD4

    $AUD5</br>
    $USD2


#### 2.5mm stereo socket

This is to connect the intervalm8r to the camera's shutter cable. The PCB has been designed to accommodate all the thru-hole PCB-mounted sockets we could buy online. You could just as easily choose in-line instead, or a directly-connected cable. Change this to a suitable connector if your camera shutter release cable uses a different type. (See ["adding the components"](https://github.com/greiginsydney/Intervalometerator/blob/master/docs/step4-pcb-assembly.md#adding-the-components) in the PCB assembly.md for more details and options.)

- [Element 14 (AU)](https://au.element14.com/lumberg/1501-05/socket-2-5mm-jack/dp/1216978)
- [Amazon](https://amzn.to/2Wo0y3R) - pack of 10, $USD3.11
- [Amazon](https://amzn.to/2WnkOmq) - pack of 5, $USD2.77

    $AUD2.00</br>
    $USD1.00

#### 3mm Green LED (optional)

As the project is presented, this LED lights when the Arduino is awake, but only if the adjacent jumper is connected (taking Arduino input A0 to ground). I used it as a generic headless debugging aid. You should be able to find this just about anywhere: your Arduino/Pi supplier, local electronics hobby store, etc.

- [Element 14 (AU)](https://au.element14.com/multicomp/mcl034gd/led-3mm-70-green/dp/1581114) - MOQ 10, $AUD2.83
- [Amazon](https://amzn.to/2P6Xrxd) - pack of 100, $USD6.36

    $AUD0.28</br>
    $USD0.06

#### Custom PCB

The custom PCB for the project is available on eBay.

- [eBay](https://www.ebay.com.au/itm/264353662332)

    $AUD15.00</br>
    $USD10.00

#### Veroboard (alternative PCB)

An alternative to the PCB will be to build the board on Veroboard, aka stripboard. (There's an image of the Veroboard prototype on the [Wiki / history](https://github.com/greiginsydney/Intervalometerator/wiki/History) page.)   

- [Jaycar (AU)](https://www.jaycar.com.au/pc-boards-vero-type-strip-95mm-x-75mm/p/HP9540)
- [Amazon](https://amzn.to/2ByUVbc)

    $AUD4.50</br>
    $USD11.00

#### Resistors

Resistors are used on the board for two purposes. They're either current-limiting the supply to the LEDs (the green one and the 2 optos) or providing pull-up or pull-down assistance to the IO pins. You should be able to find these just about anywhere: your Arduino/Pi supplier, local electronics hobby store, etc.

Green LED: 1 x 150R 1/4W

Optos: 2 x 150R 1/4W

- [Element 14 (AU)](https://au.element14.com/multicomp/mf25-150r/res-150r-1-250mw-axial-metal-film/dp/9341315) - MOQ 50, AUD$2.70
- [Amazon](https://amzn.to/33W0TPl) - pack of 100, $US5.69
    
    $AUD0.03 (ea)</br>
    $USD0.06 (ea)

Arduino pin A8: 1 x 4.7k 1/4W

Arduino pin A2: 1 x 4.7k 1/4W

- [Element 14](https://au.element14.com/multicomp/mf25-4k7/res-4k7-1-250mw-axial-metal-film/dp/9341951) - MOQ 10, AUD$0.54
- [Amazon](https://amzn.to/2MCKAkO) - pack of 100, $US5.69

    $AUD0.03 (ea)</br>
    $USD0.06 (ea)

#### 47uF electrolytic capacitor

Every supply needs some smoothing. Optional but recommended.

- [Element 14](https://au.element14.com/multicomp/mcrh35v476m6-3x11/cap-47-f-35v-20/dp/9451935?rpsku=rel3:667894&isexcsku=false)
- [Amazon](https://amzn.to/32Gf2A8) - pack of 10, $USD5.00
    
    $AUD0.30</br>
    $USD0.50
    
#### 100nF MKT polyester capacitor

Every supply needs a 100nF poly smoothing capacitor. Optional but recommended.

- [Element 14](https://au.element14.com/epcos/b32529c0104k000/cap-0-1-f-63v-10-pet-potted/dp/9750878)
- [Amazon](https://amzn.to/2W52eB2) - pack of 20, $USD4.99
    
    $AUD0.30</br>
    $USD0.25
    
#### 100nF ceramic capacitor

I really love the DeadOn RTC, however SparkFun appear to have omitted the chip manufacturer's recommended power supply capacitor. I went with a 100pF ceramic.

- [Element 14](https://au.element14.com/vishay/d101k20y5ph63l6r/ceramic-capacitor-100pf-100v-y5p/dp/1606155)
- [Amazon](https://amzn.to/35VToKb) - pack of 10, $USD8
    
    $AUD0.30</br>
    $USD0.80

#### 5.08mm / 0.2" PCB-mount sockets

These are the green power connectors for the power input and camera power output on the PCB. You want two.

- [Element 14](https://au.element14.com/camdenboss/ctb9350-2a/header-right-angle-2way/dp/3882093)
- [Newark (US)](https://www.newark.com/camdenboss/ctb9350-2a/pluggable-terminal-block-header/dp/68C9100) (MOQ=10)

    $AUD0.50 (ea)</br>
    $USD0.48 (ea)</br>
    
#### 5.08mm / 0.2" PCB-mount plugs
    
These mate with the above. You want two.

- [Element 14](https://au.element14.com/camdenboss/ctb9200-2a/terminal-block-pluggable-2pos/dp/3881854)
- [Newark (US)](https://www.newark.com/camdenboss/ctb9200-2a/terminal-block-pcb-2-position/dp/68C9081)

    $AUD1.36 (ea)</br>
    $AUD1.09 (ea)</br>
    

#### Miscellaneous

##### Header pins

- [Element 14 (AU)](https://au.element14.com/mcm/ph1-40-ua/break-away-2-54mm-40-pin-strip/dp/2802331) - strip of 40
- [Amazon](https://amzn.to/2J8ZRHW) - 10 strips, $USD5.69

    $AUD0.40</br>
    $USD0.56

##### Jumpers

You need either 4 or 6, depending on how you assemble the board.
- [Element 14](https://au.element14.com/multicomp/spc19807/mini-jumper-2-position-2-54mm/dp/1192775) - Pack of 25, $AUD
- [Amazon](https://amzn.to/2p1J3vy) - pack of 120, $USD7.88
    
    $AUD0.30</br>
    $USD0.40

##### 2.0mm Bolts (to mount the Raspberry Pi)

You might find these a challenge to source. Try a shop selling model aircraft, drones, etc.
- [Element 14](https://au.element14.com/tr-fastenings/m2-6-prstmc-z100/screw-pozi-pan-steel-bzp-m2x6/dp/1420386) - Pack of 100, $AUD2.59

    $AUD0.30</br>
    $USD

##### 2.0mm threaded spacers
- [Element 14](https://au.element14.com/ettinger/05-01-103/standoff-hex-female-brass-10mm/dp/2494574) (MOQ = 10)

    $AUD0.30</br>
    $USD

##### Backmount (for mounting the PCB to)

##### 3.0mm bolts (PCB to backmount)

##### 3.0mm (dia) spacers

##### Interconnecting wires

 Let's call it $AUD10</br>
Let's call it $USD10
    

### SUBTOTAL: AUD$212 / $USD159


## Power

#### 12V Sealed lead-acid (SLA) battery
Be careful selecting a battery. The 12V 2.2Ah SLA battery we went with only *just* fits inside the Pelican case.

- [Jaycar Electronics (AU)](https://www.jaycar.com.au/12v-2-2ah-sla-battery/p/SB2482)
- [Amazon](https://amzn.to/2MAMdiN)
    
    $AUD24</br>
    $USD15

#### 12V Solar charger

We used this "12V 6A Battery Charging Regulator for Solar Panels".

- [Jaycar Electronics (AU)](https://www.jaycar.com.au/12v-6a-battery-charging-regulator-for-solar-panels/p/AA0348)

    $AUD30

Or this 3A version will also do the trick. 

- [Jaycar Electronics (AU)](https://www.jaycar.com.au/miniature-12v-3a-pwm-solar-charge-controller/p/MP3762)

    $AUD15
    
Both these are easily sourced on the usual websites.

#### Solar panel

Choose a panel and matching charger to suit your installed environment. If you're lucky enough to have mains power, perhaps omit the panel but retain the battery and charger to sustain the system through any unexpected mains failures.

- [eBay](https://www.ebay.com.au/itm/112750149497) - 20W
- [Amazon](https://amzn.to/2pDsrKO) - 10W
- [Amazon](https://amzn.to/31C9hCe) - 25W

    $AUD49</br>
    $USD21 - 34

#### Miscellaneous

Your choice of solar panel might require some bracing or a bracket in order for it to mount to a pole. For ours we used two lengths of some 2" aluminium angle that we had to hand, resulting in a U-shaped support.


     Let's call it $AUD10</br>
Let's call it $USD10

### SUBTOTAL: AUD$113 / $USD83


## Hardware - casing and mounts

#### Pelican 1300 case

- [Amazon](https://amzn.to/2Bu9kWa)

    $AUD95</br>
    $USD60

#### CCTV Camera Mount


 $AUD15</br>
$USD

#### Cable entry gland

You only need two holes in the box - one to let the light in, and another for the power. For the power input, you'll need some sort of gland to provide a water-tight seal.

You should be able to source these from your nearest electrical wholesaler, hobbyist electronics shop, or maybe a marine supplies shop (if you're near water).

- [Cabac (AU)](https://www.cabac.com.au/product-specs/13450510/GN12S)
- [Amazon](https://amzn.to/2N2nQK1) - pack of 6, $USD6

    $AUD2 (est)</br>
    $USD1

#### Ram Mounts

If your budget allows for it, check out some of the mounting options in the Ram Mounts range. Their ["C Size" mounts](https://www.rammount.com/search?query=c+size) will take up to a 5kg (~10lb) load.



## SUBTOTAL: $AUD112 / $USD76

<br/>

### Declaration:
The Amazon links above are affiliate links. We may earn a small commission from purchases, however you pay no more for this.
