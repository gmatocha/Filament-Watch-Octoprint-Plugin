Placeholder.

# Filament Watch Helper Functions

## Function:
- FilamentWatchExtrudedInfo
## Returns:
Dictionary containing the following values:
- gcodeExtrudedlLen (float, mm):
	Latest extruded length per GCODE sent to the printer. Note, depending on queueing and planning in the printer, this length may not be acted upon for some time.
	
- measuredExtrudedLen (float, mm)
Current extruded length reading from the rotary encoder, plus drift correction.

- gcodeForecastLen (float, mm)
Filament Watches' best guess at the real current extruded length. This is what is used for comparisons to determine alarm conditions.
- printing (bool)
Whether there is a print in progress.

- armed (bool)
Whether Filament Watch Alarm has been armed. May be disarmed because the print hasn't run long enough yet
- arm_alarm_in_sec
- alarm
- paused
- alarmWindowWidth


<!--stackedit_data:
eyJoaXN0b3J5IjpbLTI2NTY1ODk5Nl19
-->