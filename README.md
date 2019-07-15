# Filament Watch Octoprint Plugin

Initial work based on the [Octoprint-Filament-Reloaded](https://github.com/kontakt/Octoprint-Filament-Reloaded) plugin by kontakt.
Initial work based on the [Filament Watch](https://github.com/MoonshineSG/Octoprint-Filament) plugin by RLLynch.

## Required sensor

Using this plugin requires a filament sensor. The code is set to use the Raspberry Pi's internal Pull-Up resistors, so the switch should be between your detection pin and a ground pin.

This plugin is using the GPIO.BOARD numbering scheme, the pin being used needs to be selected by the physical pin number.

## Features

* Execution of custom GCODE when out of filament detected.
* Optionally pause print when out of filament.

## Installation

* Manually using this URL: https://github.com/p

## Configuration

After installation, configure the plugin via OctoPrint Settings interface.
