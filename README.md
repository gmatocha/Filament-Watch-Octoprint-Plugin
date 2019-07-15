# OctoPrint-FilamentSensor-ng

I made this because [Octoprint-Filament-Reloaded](https://github.com/kontakt/Octoprint-Filament-Reloaded) would segfault and I wanted more options.

[OctoPrint](http://octoprint.org/) plugin that integrates with a filament sensor hooked up to a Raspberry Pi GPIO pin and allows the filament spool to be changed during a print if the filament runs out.

Future developments are planned to include multiple filament sensors and pop-ups.

Initial work based on the [Octoprint-Filament-Reloaded](https://github.com/kontakt/Octoprint-Filament-Reloaded) plugin by kontakt.
Initial work based on the [Octoprint-Filament](https://github.com/MoonshineSG/Octoprint-Filament) plugin by MoonshineSG.

## Required sensor

Using this plugin requires a filament sensor. The code is set to use the Raspberry Pi's internal Pull-Up resistors, so the switch should be between your detection pin and a ground pin.

This plugin is using the GPIO.BOARD numbering scheme, the pin being used needs to be selected by the physical pin number.

## Features

* Configurable GPIO pin.
* Debounce noisy sensors.
* Support norbally open and normally closed sensors.
* Execution of custom GCODE when out of filament detected.
* Optionally pause print when out of filament.

## Installation

* Manually using this URL: https://github.com/Red-M/Octoprint-Filament-Sensor-ng/archive/master.zip

## Configuration

After installation, configure the plugin via OctoPrint Settings interface.
