# Filament Watch Octoprint Plugin

Initial work based on the [Filament Watch](https://github.com/rllynch/filament_watch) plugin by RLLynch.
![Monitor](https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/blob/master/images/Monitor.png)

[Are you sure you want to do this? ;)](#Using_Filament_Watch_reliably)

## Features

* Pause, cancel, or just send GCODE when filament stops
* Automatic search for attached Arduino/rotary encoder
* Adjustable alarm boundaries
* USB connection to Octoprint/Octopi

## Required sensor

Using this plugin requires a rotary encoder sensor, and an Arduino micro controller to manage the encoder. The enclosure STL files are designed for a rotary encoder with a 38mm (dia) x 35.5mm body, 6mm shaft and capable of running on 5v. The pulses/revolution of the encoder is not very critical; the encoder is run in quadrature mode, so the rated P/R will be multiplied by four. So even with a 100 P/R encoder and a 23mm encoder wheel, the resolution would be under .2mm - more than enough for accurate monitoring.

* Note if you do use an encoder with other than 600P/R, the DPM value in the Arduino code needs to be modified. Future versions will make this configurable through Octoprint.


## Purchased Parts:

1. Quadrature encoder:
  * Verified: Signswise 600p/r Incremental Rotary Encoder Dc5-24v Wide Voltage Power Supply 6mm Shaft [[Amazon link]](http://www.amazon.com/gp/product/B00UTIFCVA?psc=1&redirect=true&ref_=oh_aui_detailpage_o09_s00)
* Pending verification: 
* Other encoders may work, providing you come up with a suitable enclosure.

2. Arduino controller supporting 5V and Serial over USB:
* Verified: Adafruit Metro Mini 328 - 5V 16MHz [[Adafruit link]](https://www.adafruit.com/product/2590) [[Pinouts]](https://learn.adafruit.com/adafruit-metro-mini/pinouts)
* Pending Verification: (7/2019) Itsy Bitsy 32u4 5V [[Adafuit link]](https://www.adafruit.com/product/3677)[[Pinouts]](https://learn.adafruit.com/introducting-itsy-bitsy-32u4/pinouts)

3. USB A to Micro-B cable for Arduino [[Adafuit link]](https://www.adafruit.com/product/592)

4. Optional: 2 x 0.1" pitch header blocks [[Adafruit link]](https://www.adafruit.com/products/2142)

5. Optional: (depending on case you use) 608 ball bearing [[Amazon link]](https://www.amazon.com/Groove-Bearing-Bearings-Skateboard-Printer/dp/B07FGVFN6F). These are the same bearings used in skates and skateboard wheels. You don't need anything fancy here - don't spend money on ceramic or high abec bearings. Old dead ones will work as long as they roll smoothly.

6. Optional: 30mm Rotary Encoder wheel [[Ali Express Link]](https://www.aliexpress.com/item/32974396980.html). The enclosure stl files below include a wheel stl that is designed for the enclosure, and is usually printed in a soft material like TPU/Ninjaflex. Manufactured wheels are higher quality, but generally not so much as to affect Filament Watch. If you do use a manufactured wheel, choose a case that is designed for it.


## Printed parts - Enclosures and wheels:

There are several options for the encoder housing, depending on what will work with your setup.

1. RLLynch's [base and wheel](http://www.thingiverse.com/thing:936521) and optional [mini metro enclosure](http://www.thingiverse.com/thing:936519)

2. [My housing for the D6](https://www.thingiverse.com/thing:3746948)


## Wiring

### Wiring instructions for the Metro Mini 328 or Itsy Bitsy 5v
  Optionally solder the header blocks first.
  (Note check your enclosure to see if it's compatible with the header blocks)

1. Encoder red (power) - 5V
2. Encoder black (ground) - GND
3. Encoder green (output 1) - digital pin 3
4. Encoder white (output 2) - digital pin 2

![](https://github.com/rllynch/filament_watch/blob/master/images/metro_mini_328_wiring.jpg)



### Wiring instructions for the Itsy Bitsy (pending)


## Installation

1. Install the plugin in Octoprint Settings->Plugin Manager:
* Manually using this URL: https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin
* From the [Octoprint Plugin repositry](https://plugins.octoprint.org/) (pending)

2. Compile and flash Arduino/filament_watch/filament_watch.ino into the Metro Mini using either the Arduino IDE, or the command line scripts shown below:

3. Connect the Metro Mini by USB to the computer running OctoPrint. Attach the wheel to the encoder and place it in the base. Feed the filament through the base.


## Configuration

After installation, configure the plugin via OctoPrint Settings interface.
![Settings](https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/blob/master/images/Settings.png)
* Allowed Deviation (mm): If monitored length is more or less than the forecast gcode, 

### Pause and Resume Scripts
In addition to preventing wasted filament after a feed problem, in many cases Filament Watch allows problems to be corrected without destroying the print in progress. To do this, you'll need to use OctoPrints GCODE Scripting feature to move the print head out of the way on pause, then return it to the exact same location when the print resumes.

Copy the scripts below into the **After print job is paused**, and **Before print job is resumed** fields in *Octoprint->Settings->GCODE Scripts*

![GCODE Scripts](https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/blob/master/images/PauseResumeScript.png)


#### After print job is paused
```
; From 
{% if pause_position.x is not none %}
; relative XYZE
G91
M83

; retract filament, move Z slightly upwards
G1 Z+5 E-1.5 F4500

; absolute XYZE
M82
G90
; move to a safe rest position, adjust as necessary
G1 X0 Y0

; Home X and Y only
;G28 X Y

;disable heater, but not bed because we want to keep adhesion
{% snippet 'disable_hotends' %}

{% endif %}

; play a jaunty tune (if your printer speaks)
M300 S440 P400
M300 S660 P400
M300 S660 P1000
M300 S440 P1000
M300 S660 P1000
M300 S440 P1000
```

#### Before print job is resumed
```
{% if pause_position.x is not none %}

; turn filament heaters back on
{% for tool in range(printer_profile.extruder.count) %}
    {% if pause_temperature[tool] and pause_temperature[tool]['target'] is not none %}
        {% if tool == 0 and printer_profile.extruder.count == 1 %}
            M109 T{{ tool }} S{{ pause_temperature[tool]['target'] }}
        {% else %}
            M109 S{{ pause_temperature[tool]['target'] }}
        {% endif %}
    {% else %}
        {% if tool == 0 and printer_profile.extruder.count == 1 %}
            M104 T{{ tool }} S0
        {% else %}
            M104 S0
        {% endif %}
    {% endif %}
{% endfor %}

; relative extruder
M83

; prime nozzle
G1 E-5 F4500
G1 E5 F4500
G1 E5 F4500

; absolute E
M82
; absolute XYZ
;G90

; reset E
G92 E{{ pause_position.e }}

; move back to pause position XY
G1 X{{ pause_position.x }} Y{{ pause_position.y }} F1500
; then move back to pause position Z to minimize risk of bumping part off bed
G1 Z{{ pause_position.z }} F1500

; reset to feed rate before pause if available
{% if pause_position.f is not none %}G1 F{{ pause_position.f }}{% endif %}
{% endif %}
```

## Using Filament Watch

![Monitor](https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/blob/master/images/GraphOnly.png)

### The Graph:
The graph on the Filament Watch tab shows four values:
* GCODE Commanded (black): This is the extruded length sent to the printer. Note it deviates from reality because of queuing and the time the printer takes to execute the moves. On large slow prints this deviation can be quite large.
* Measured Len (blue): This is the measurement from the rotary encoder, plus a drift correction that is applied on a regular interval (controlled by Drift Correction Interval in [settings](#Configuration)). You can see a drift correction here at -95 seconds. Drift Correction prevents false alarm triggers from accumulated small errors on large prints.
* GCODE Forecast (yellow): This is Filament Watch's best guess where how much filament has been extruded in real-time. This is the line that Filament Watch uses when determining whether an alarm condition has occurred.
* Alarm Boundary (green area): GCode Forecast +/- Allowed Deviation from [settings](#Configuration) plus an additional deviation allowance calculated from the difference between the GCODE Forecast and CGODE Commanded. The instantaneous value is shown in Allowed Deviation field. If Measured Len exceeds this value, an alarm is triggered.

![Monitor](https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/blob/master/images/TableOnly.png)

### Values Table
### Log
The section at the bottom shows the last 10 Filament Watch log lines, including drift corrections. See [](#Tuning) below.

## Tuning
As the print runs, Filament Watch will monitor accumulated errors and make suggestions for dialing in the exact rotary encoder diameter. Check this test in the Filament Watch logs:
![GCODE Scripts](https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/blob/master/images/Monitor_SuggestedDia.png)

Notes:
* At the beginning of the print, this suggested diameter will be way off, but will close in on the correct value the longer the print runs.
* Ironically, prints with many short moderately paced moves will produce a more accurate suggested diameter than prints with long slow extrusions. This is because forecasting must be used on the long slow prints, while short fast prints mean sent and measured lengths stay closer.


## Using Filament Watch reliably
I'll be honest with you...get ready.
You probably don't want to use Filament Watch. Boom.
 Filament monitoring seems like a no-brainier right? *Throw in a rotary encoder....measure what moves and compare to what's supposed to move...simple right?*
Here's what they're not telling you. If the monitor is not SIGNIFICANTLY more reliable than your prints, it's worse than useless. Let's say 1 in 20 - 5% - of our prints fail because of a condition Filament Watch might detect (and yes, we're being honest - there are many more). Ok great, we can perhaps save half of those 1 in 20 prints. But if Filament Watch has the same error rate - false positive errors on 1 in 20 prints - then you will actually have MORE failed prints using Filament Watch even if it accurately detects true failures. For this reason Filament Watch has to be significantly more reliable than the printer itself to at least not be a hindrance. Throw in the fact that there are so many printers, so many different firmware with different caching buffer sizes and planning schemes, and so many physical configurations, and you start to get a sense of scale of this problem. But wait it gets worse - then there's the slicer, the print settings, and even the model itself.  All this means what Octoprint sends is almost never synchronized with the real world (which is what Filament Watch sees) sometimes it's not. even. close. At this point the brain melts.

So is all lost? No, not at all, but expectations must be set.
Here are my suggestion for success with Filament Watch:
* Until you have Filament Watch dialed in, set Alarm Action [in settings](#Configuration) to GCODE only. Then set the GCODE script to nothing or just beep (if your printer speaks) to notify you of an alarm. Here's some beep code for Marlin based printers:

 

    M114 S600 P700
    M114 S400 P700
    M114 S600 P700
* Don't rely on Filament Watch until you've verified it with the same or similar models. What does "similar" mean?
	- Same printer and slicer? Obviously
	- Similar speed? Yes
	- Same layer height? Yes
	- Similar model? Yes. Huh? Why the model itself? Because a Benchy with its small intricate moves will look very different to Filament Watch than a full volume cube given all the same settings.
* Wide alarm tolerances are OK. The difference between a 25mm alarm boundary and a 50mm boundary might only delay an alarm by 30 seconds...which won't make a difference between a salvageable and failed print. But it might prevent a false alarm that does fail the print.
* The same goes for the drift correction interval - a fast (say 120 second) drift correction might delay some alarms, but will make false alarms less likely.

#### Wow, that was all doom and gloom. Is there any reason TO use Filament Watch?

Yes. 

<!--stackedit_data:
eyJoaXN0b3J5IjpbMTU0MjQ0ODUxMSwyODE2MTAwMiwtMTEyOD
c2MjE4MSwtMTI2MjQ2MTkxNV19
-->