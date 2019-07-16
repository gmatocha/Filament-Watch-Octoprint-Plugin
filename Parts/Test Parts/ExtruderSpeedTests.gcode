;FLAVOR:Marlin

; Duplicator 6 / Monoprice Maker Ultimate Start Script V3
M107 ; start with the fan off
G28 ; home
G1 Z50 F3600 ; move the platform 50mm down from home
G0 X100 Y30 ; move the head to middle away from edge for easy viewing
G92 E0 ; zero the extruded length


; Set these temps for your material
M104 S245	; set temp
M109 S245	; wait for temp

G91 ; Relative positioning


M117 25 mm/s...
G4 S3				; wait 3 sec
G1 E34.5 F1500		; 25 mm/s
G4 S2.4				; wait estimated extrusion time plus one sec

M117 23 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F1380		; 23 mm/s
G4 S2.5				; wait estimated extrusion time plus one sec

M117 20 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F1200		; 20 mm/s
G4 S2.75				; wait estimated extrusion time plus one sec

M117 15 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F900		; 15 mm/s
G4 S3.3				; wait estimated extrusion time plus one sec

M117 5 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F300		; 5 mm/s
G4 S7.9				; wait estimated extrusion time plus one sec

M117 2 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F120		; 2 mm/s
G4 S18.25			; wait estimated extrusion time plus one sec

M117 1 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F60		; 1 mm/s
G4 S35.5			; wait estimated extrusion time plus one sec

M117 3/4 mm/s...		; Display
G4 S3				; wait 3 sec
G1 E34.5 F45		; .75 mm/s
G4 S47				; wait estimated extrusion time plus one sec

M117 1/2 mm/s...	; Display
G4 S3				; wait 3 sec
G1 E34.5 F30		; .5 mm/s
G4 S70				; wait estimated extrusion time plus one sec

M117 1/4 mm/s...	; Display
G4 S3				; wait 3 sec
G1 E34.5 F15		; .25 mm/s
G4 S140				; wait estimated extrusion time plus one sec

M117 Complete		; Display
G4 S1				; wait 1 sec

; Duplicator 6 / Monoprice Maker Ultimate Stop Script V2
G1 E-1.5 F500 ; retract the filament to release some of the pressure

M104 S0 ; turn off heater
M140 S0 ; turn off bed
M106 S0 ; turn off part fan
M84 ; disable stepper motors
