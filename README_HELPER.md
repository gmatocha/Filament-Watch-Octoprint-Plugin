
# Filament Watch Helper Functions

## Function:
- **FilamentWatchExtrudedInfo**
## Returns:
Dictionary containing the following values:
- **gcodeExtrudedlLen** (float, mm):
	Latest extruded length per GCODE sent to the printer. Note, depending on queueing and planning in the printer, this length may not be acted upon for some time.
	
- **measuredExtrudedLen** (float, mm):
Current extruded length reading from the rotary encoder, plus drift correction.

- **gcodeForecastLen** (float, mm):
Filament Watches' best guess at the real current extruded length. This is what is used for comparisons to determine alarm conditions.

- **printing** (bool)
Whether there is a print in progress.

- **armed** (bool):
Whether Filament Watch Alarm has been armed. May be disarmed because the print hasn't run long enough yet, or manually disarmed by the user.
- **arm_alarm_in_sec** (int, seconds):
How many seconds until the alarm will arm. Will be 0 once armed, or if disarmed by the user.

- **alarm** (bool):
Whether Filament Watch has triggered an alarm.

- **paused** (bool):
Whether the print is paused.

- **alarmWindowWidth** (float, mm):
How far measuredExtrudedLen can be from gcodeForecastLen before triggering an alarm. The base for this number is the *Allowed Deviation (mm)* setting, plus the difference between commanded and forecast gcode. This widens the alarm window when there is large asynchronicity between sent gcode and the real world to prevent false alarms. This values decays back to Allowed Deviation at approximately .1mm/sec. 



<!--stackedit_data:
eyJoaXN0b3J5IjpbLTE5OTQxMDI4ODldfQ==
-->