# Filament Watch Octoprint Plugin

Initial work based on the [Filament Watch](https://github.com/rllynch/filament_watch) plugin by RLLynch.

## Features

* Pause, cancel, or just send GCODE when filament stops
* Automatic search for attached Arduino/rotary encoder
* Adjustible alarm boundries
* USB connection to Octoprint/Octopi

## Required sensor

Using this plugin requires a rotary encoder sensor, and an Arduino micro controller to manage the encoder. The enclosure STL files are designed for a rotary encoder with a 38mm (dia) x 35.5mm body, 6mm shaft and capable of running on 5v. The pulses/revolution of the encoder is not very critical; the encoder is run in quadrature mode, so the rated P/R will be multiplied by four. So even with a 100 P/R encoder and a 23mm encoder wheel, the resolution would be under .2mm - more than enough for accurate monitoring.

* Note if you do use an encoder with other than 600P/R, the DPM value in the Arduiono code needs to be modified. Future versions will make this configurable through Octoprint.



## Purchased Parts:

1) Quadrature encoder. The STL files are designed for a rotary encoder with a 38mm (dia) x 35.5mm body, 6mm shaft and capable of running on 5v, such as:
Verified: "Signswise 600p/r Incremental Rotary Encoder Dc5-24v Wide Voltage Power Supply 6mm Shaft" [[Amazon link]](http://www.amazon.com/gp/product/B00UTIFCVA?psc=1&redirect=true&ref_=oh_aui_detailpage_o09_s00)
  Pending verification: 
  
  Other encoders may work, providing you come up with a suitable enclosure.

2) Arduino controller supporting 5V and Serial over USB:
  Verified: Adafruit Metro Mini 328 - 5V 16MHz [[Adafruit link]](https://www.adafruit.com/product/2590)
  Pending Verification (7/2019): Itsy Bitsy 32u4 5V [[Adafuit link]](https://www.adafruit.com/product/3677)

3) USB A to Micro-B cable for Arduino [[Adafuit link]](https://www.adafruit.com/product/592)

4) Optional: 2 x 0.1" pitch header blocks [[Adafruit link]](https://www.adafruit.com/products/2142)

5) Optional: (depending on case you use) 608 ball bearing [[Amazon link]](https://www.amazon.com/Groove-Bearing-Bearings-Skateboard-Printer/dp/B07FGVFN6F). You don't need anything fancy here - don't spend money on ceramic or high abec bearings. Old dead ones will work as long as they roll smoothly.


## Printed parts - Enclosures and wheels:

There are seveal options for the encoder housing, depending on what will work with your setup.

1) RLLynch's [base and wheel](http://www.thingiverse.com/thing:936521) and optional [mini metro enclosure](http://www.thingiverse.com/thing:936519)

2) [My housing for the D6](https://www.thingiverse.com/thing:3746948)


## Wiring



### Wiring instructions for the Metro Mini 328
  Optionally solder the header blocks first.
  (Note check your enclosure to see if it's compatible with the header blocks)

4.1) Encoder red (power) - 5V

4.2) Encoder black (ground) - GND

4.3) Encoder green (output 1) - digital pin 3

4.4) Encoder white (output 2) - digital pin 2

![](https://github.com/rllynch/filament_watch/blob/master/images/metro_mini_328_wiring.jpg)

5) Connect the Metro Mini by USB to the computer running OctoPrint. Attach the wheel to the encoder and place it in the base. Feed the filament through the base.

6) Check out this git repository onto the computer running OctoPrint.

```
git clone https://github.com/rllynch/filament_watch.git
```

7) Compile and flash arduino/filament_watch/filament_watch.ino into the Metro Mini using either the Arduino IDE, or the command line scripts shown below:

### Wiring instructions for the Itsy Bitsy (pending)


## Installation

* Manually using this URL: https://github.com/p
* From the [Octoprint Plugin repositry](https://plugins.octoprint.org/) (pending) 

## Configuration

After installation, configure the plugin via OctoPrint Settings interface.
