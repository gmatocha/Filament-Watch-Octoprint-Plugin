# coding=utf-8
from __future__ import absolute_import

import sys
import octoprint.plugin
import octoprint.util
from octoprint.events import Events
from collections import OrderedDict
import re
import time
import math
import serial
import serial.tools.list_ports

class filamentwatchPlugin(octoprint.plugin.StartupPlugin,
							 octoprint.plugin.EventHandlerPlugin,
							 octoprint.plugin.TemplatePlugin,
							 octoprint.plugin.SettingsPlugin,
							 octoprint.plugin.AssetPlugin,
							 octoprint.plugin.SimpleApiPlugin):


	# A small array (10 lines) of log messages will be displayed on the Filament Watch tab.
	def FWLog(self, msg):
		'''Append a log message'''
		timestamp = time.strftime('%H:%M:%S', time.localtime())
		logstr = '%s: %s<br/>\n' % (timestamp, msg)
		self.log_msgs.insert(0, logstr)
		if len(self.log_msgs) > 10:
			self.log_msgs.pop()
		# lets add it to Octoprings log too
		self._logger.info(msg)


	# uses octoprints built in messaging system
	# to send current data set to the UI
	def Send2ClientDataUpdate(self, SummaryText):
			
		stats = {
			# convert the times to ms for the java side
			'time': int(time.time() * 1000),
			'gcode': self.ExLen_gcode,
			'actual': self.ExLen_ROT,
			'gcode_forecast': self.ExLen_gcode_forecast,
			'gcode_forecast_predictions': list(self.gcode_forecast.items()),
			'history_length': self.windowduration,
			'alarm': self.alarm,
			'printing': self.printing,
			'PrintPaused': self.PrintPaused,
			'armed': self.armed,
			'arm_alarm_in_sec': self.AlarmCountdown,
			'ManuallyDisarmed': self.ManuallyDisarmed,
			'ErrorOnDeviationmm': self.ErrorOnDeviationmm + self.DeviationWindow,
			'FeedRate': self.Feedrate,
			'summary': SummaryText,
			'log_msgs': self.log_msgs
			}

		# no Nones!
		for k in stats:
			if stats[k] is None:
				stats[k] = 0

		data = dict(type='filament_data', data=stats)

		self._plugin_manager.send_plugin_message(self._identifier, data)
		
		
	# uses octoprints built in messaging system
	# to send current data set to the UI
	def SendPNotify(self, Title, Text, type = 'info', hide = False):
		PNotify = {
			'title': Title,
			'text': Text,
			'type': type,
			'hide': hide
		}
		data = dict(type='PNotify', data=PNotify)

		self._plugin_manager.send_plugin_message(self._identifier, data)

		
	# Special message that just resets the print data on the client side
	def Send2ClientStarted(self):
		data = dict(type='Starting')

		self._plugin_manager.send_plugin_message(self._identifier, data)
	

	def ExceptionHandler(self, location, msg = ""):
		exc_type, exc_obj, exc_tb = sys.exc_info()
		message = "Exception " + str(exc_type) + " in " + location + " on line " + str(exc_tb.tb_lineno) + " " + msg
		self.FWLog(message)


	# Timer event (every second) to do the acutal work of reading the count from
	# the arduino, and all the processing that follows - checking if alarm, etc.
	def ROT_Worker(self):
		try:
			self._logger.info("Worker started.")
		
			if not self.sensor_enabled or not self.printing:
				self._logger.info("Worker Exited becuse disabled or not printing.")
				return

			
			if self.PrintPaused:
				self._logger.info("Worker Exited becuse waiting for print to resume.")
				return

			now = int(time.time())

			# if ExLen_ROT is none, then we must have just started a print.
			# Let's use this opportunity to do some setup.
			if self.ExLen_ROT is None:
				self.ExLen_ROT = 0
				self.ArmAlarmTime = now + self.ArmAlarmDelay
				self.driftCorrectionTime = now + self.driftCorrectionInterval
				self.FWLog("Starting monitor.")

			pos = 0
		
			self.RotaryEncoder.reset_input_buffer()
			self.RotaryEncoder.write("GETPOS\n")
			rcv = self.RotaryEncoder.readline().decode('utf-8', 'ignore')

			splitline = rcv.split()
			if (len(splitline) == 3 and splitline[0] == "FWPos" and splitline[2] == "FWPos"):
				pos = float(splitline[1])

				# Drift Correction - also used to force filament sensor back to gcode after resume
				if self.driftCorrectionTime and now >= self.driftCorrectionTime:
					# set the next time to correct drift
					self.driftCorrectionTime = now + self.driftCorrectionInterval
					
					self.DriftCorrection = self.ExLen_gcode_forecast - pos
					DiaCorrection = (self.ExLen_gcode_forecast/pos) * self.WheelDia
					self.FWLog("Correcting for drift of " + str(-self.DriftCorrection) + " Suggested dia:" + str(DiaCorrection))
					

				self.ExLen_ROT = pos + self.DriftCorrection
			else:
				# Uh Oh - probably a serial error
				# It might seem more logical to error out at this point,
				# but in reality serial errors can be more common than you might think - 
				# I've seen several in a long print on my setup.
				# Usually it just happens once at a time, so let's
				# keep going with the last value. If it repeats several times,
				# we'll hit the alarm condition within a few seconds anyway.
				self.FWLog("Didn't receive FWPos delims from encoder:" + rcv)

				# No change to ExLen_ROT
			

			# Time to arm the alarm?
			if self.ManuallyDisarmed:
				self.armed = False
				self.AlarmCountdown = 0
			else:
				if not self.armed:
					# this seems redundant, but we're also using AlarmCountdown for display purposes
					self.AlarmCountdown = int(self.ArmAlarmTime - now)
				
					if self.AlarmCountdown <= 0:
						self.AlarmCountdown = 0
						self.armed = True
						if (self.CorrectDriftOnArm):
							#This just forces the Drift Correction code below to fire
							self.driftCorrectionTime = now
							


			# find the "now" value and take everything older out of the forecast...it's not forepast
			oldest = next(iter(self.gcode_forecast.keys()))
			for t in range (now, oldest-1, -1):
				if t in self.gcode_forecast:
					self.ExLen_gcode_forecast = self.gcode_forecast[t]
					
					# wack everything older
					for t2 in range (t-1, oldest-1, -1):
						if t2 in self.gcode_forecast:
							del self.gcode_forecast[t2]
					
					break
				

			# use the difference between commanded and current extrusion as an indicator
			# of how wide the tolerance should be
			deltaE = abs(self.ExLen_gcode_forecast - self.ExLen_gcode)
			if deltaE > self.DeviationWindow:
				self.DeviationWindow = deltaE

			self._logger.info("Worker: Armed: " + str(self.armed) + " ExLen_gcode: " +\
					str(self.ExLen_gcode) + " ExLen_gcode_forecast: " + str(self.ExLen_gcode_forecast) +\
					" ROT:" + str(self.ExLen_ROT) + " Dev:" + str(self.ErrorOnDeviationmm) + " now " + str(now) )

			#The "main check" for an error is here
			if self.armed and not self.alarm \
					and abs(self.ExLen_gcode_forecast - self.ExLen_ROT) > (self.ErrorOnDeviationmm + self.DeviationWindow):
				self.alarm = True
				self.FWLog("Alarm Triggered.")
				
				if (self.alarmaction == 'cancel'):
					self.FWLog("Canceled Print on alarm condition.")
					self._printer.cancel_print()
					self.SendPNotify("Filement Watch", "Canceled the print on error.", type="error")
					

				elif(self.alarmaction == 'pause'):
					self._logger.info("Worker: Pausing print.")

					# we're sending this message first to get the display updated - it won't update after paused.
					self.FWLog("Print Paused - waiting for Resume")
					self.PrintPaused = True
					self.Send2ClientDataUpdate("Monitor enabled - Print Paused")
					self._printer.pause_print()
					self.SendPNotify("Filement Watch", "Paused the print on error.", type="error")
					

				if self.no_filament_gcode and len(self.no_filament_gcode):
					self._logger.info("Worker: Sending out of filament GCODE")
					self._printer.commands(self.no_filament_gcode)
					self.SendPNotify("Filement Watch", "Alarm Triggered. Out of filament GCODE sent.", type="error")
					

			# The deviation window widens after large slow extrusions,
			# then narrows back down to the configured allowed deviation
			# This is the code that narrows it back down.
			if self.DeviationWindow:
				self.DeviationWindow -= self.DeviationWindowDecayMmPerSec
				if self.DeviationWindow < 0:
					self.DeviationWindow = 0
			
			# Now tell the client side what's happening
			self.Send2ClientDataUpdate("Monitoring Enabled")
			
			self._logger.info("Worker: Got srting from encoder '" + rcv + "'. Final extruded length: " + str(self.ExLen_ROT))

		except Exception as ex:
			self.ExceptionHandler("Worker Thread:")


	# This "Zeros" all the rotary encoder variables before a print
	def ResetRotaryVars(self):
		self.ROT_ExtrudedLenBase = 0
		self.Feedrate = 0
		self.LastX = -1
		self.LastY = -1
		self.LastZ = 0
		self.LastE = 0
		
		self.DriftCorrection = 0
		
		self.DeviationWindow = 0
		
		# jese this is arbitrary...I'd like to make it dynamic and based on the print,
		# but not sure how to approach that at this time, so make it pretty tolerant
		self.DeviationWindowDecayMmPerSec = 0.1
		
		self.printing = False
		self.PrintPaused = False
		self.alarm = False
		self.armed = False
		self.ManuallyDisarmed = False
		self.AlarmCountdown = 0
						
		self.gcode_history = []
		self.actual_history = []
		self.gcode_forecast = OrderedDict()

		# latest RECEIVED extruded length according to the GCODE...but this may happen in the future
		self.ExLen_gcode = 0
		# best guess of the actially extruded length after some calulations based on the GCODE
		self.ExLen_gcode_forecast = 0
		# current extruded length reported by the Rotary encoder
		self.ExLen_ROT = None
		
		
		self.log_msgs = []

		# just some processing flags
		self.WaitForFirstMove = False
		
		
		
	def ForceDriftCorrectionNow(self):
		self.driftCorrectionTime = time.time()


	def __init__(self):
		self.sensor_enabled = False
		self.ResetRotaryVars()
		self.GCODESplitter = re.compile('([A-Z])')

		
	def setup_serial(self):
		self._logger.info("Setting up Rotary Encoder on:" + self.USBDevice + " baud:" + str(self.baudrate))
		
		try:
			if self.RotaryEncoder:
				self.RotaryEncoder.close()
		except:
			self._logger.info("Serial port was already closed.")
		
		try:
			self.RotaryEncoder = serial.Serial(self.USBDevice, baudrate=self.baudrate, timeout=0.5, write_timeout = 0.5)
			# hack to allow connect to complete - see https://github.com/pyserial/pyserial/issues/329
			time.sleep(2)
			
			self.RotaryEncoder.write("StopLoop\n")
			rcv = self.RotaryEncoder.readline()
			self._logger.info("Command Response: " + rcv)

			self.RotaryEncoder.write("SetWheelDia:" + str(self.WheelDia) + "\n")
			rcv = self.RotaryEncoder.readline()
			self._logger.info("Command Response: " + rcv)
			
			self.RotaryEncoder.write(self.RotPositiveDir + "\n")
			rcv = self.RotaryEncoder.readline()
			self._logger.info("Command Response: " + rcv)
			
			self.RotaryEncoder.flush()
			self.RotaryEncoder.reset_input_buffer()
			self._logger.info("Serial port successufully opened.")
			
		except:
			self.close_serial()
			self._settings.set(["sensor_enabled"], False)
			self._logger.info("Opening port :" + self.USBDevice + " baud:" + str(self.baudrate) + " failed. Filament Watch disabled")
			
		return

	def close_serial(self):
		self._logger.info("Closing Rotary Encoder on:" + self.USBDevice)
		
		try:
			if self.RotaryEncoder:
				self.RotaryEncoder.close()
		except:
			self._logger.info("Serial port was already closed.")
			
		self.RotaryEncoder = None
			
		return


	def SettingsToSelf(self):
		# This is a little wacky. We're using the defaults to get the names and types of the settings
		# querying settings for the current value, and casting that to the types from defaults.
		# the magic here is setattr, which is setting (even creating) vars in self based on the keys from defaults...
		# ...which are strings. How cool is Python? If you do away with the type casting, this is can be just four lines of code. 
		#
		# So the trick with this code is to just define your settings in the get_default_setting function, and
		# they will automagically be created in self, and set with the values the users set. Single point of maintenance.
		try:
			defaults = self.get_settings_defaults()
			for k in defaults:
				# we're going to enforce the type as it is in the defaults, because we don't know where our setting value has been.
				# I've seen ints come back as strings...go figure.
				t = type(defaults[k])
				v = t(self._settings.get([k]))
				self._logger.info("Got setting " + str(k) + "=" + str(v) + " type " + str(type(v)))
				setattr(self, k, v)
		except:
			self._logger.info("Oops...iterating settings items failed.")


	def on_after_startup(self):
		self._logger.info("Filament Watch started")
		self.SettingsToSelf()

	def SearchForFilamentWatch(self, ExcludePorts = []):
		self._logger.info("Filament Watch started")

		try:
			ports = serial.tools.list_ports.comports()
			for port in ports:
				self._logger.info("Found Serial Device :" + str(port))
				
			for port in ports:
				if port.device in ExcludePorts:
					self._logger.info("Skipping Port: " + str(port))
					continue
			
				self._logger.info("Checking for Filament Watch on :" + str(port))

				try:
					testport = serial.Serial(port.device, baudrate = self.baudrate, timeout = 1, write_timeout = 1)
					
					# hack to allow connect to complete - see https://github.com/pyserial/pyserial/issues/329
					time.sleep(2)
					
					testport.reset_input_buffer()

					for count in range(2):
						self._logger.info("Checking for Filament Watch on :" + str(port))

						testport.write("FindFilamentWatch\n")
						testport.flush()
					
						rcv = testport.read(len("FilamentWatchHere!\n")).decode('utf-8', 'ignore')
						rcv = rcv.strip()
						self._logger.info("Got '" + rcv + "' from " + str(port))
						if rcv == "FilamentWatchHere!":
							self.FWLog("Found FilamentWatch arduino on " + str(port))
							testport.close()
							return port.device
						
				except serial.SerialException:
					self._logger.info("Serial exception of some sort...guess FilamentWatch isn't here. Next!")
				except serial.SerialTimoutException:
					self._logger.info("Write timeout...guess FilamentWatch isn't here. Next!")
				
				try:
					testport.close()
				except:
					pass
			
		except:
			self.ExceptionHandler("on_after_startup")
			
		return FWPort



	# Helper Function - for other plugins that might want to know the measured extruded length
	def InfoHelper(self):
		stats = {
			'gcodeExtrudedlLen': self.ExLen_gcode,
			'measuredExtrudedLen': self.ExLen_ROT,
			'gcodeForecastLen': self.ExLen_gcode_forecast,
			'printing': self.printing,
			'armed': self.armed,
			'arm_alarm_in_sec': self.AlarmCountdown,
			'alarm': self.alarm,
			'paused': self.PrintPaused,
			'alarmWindowWidth': self.ErrorOnDeviationmm + self.DeviationWindow,
			}
		return(stats)
			

	def get_settings_defaults(self):
		return ({
			# important to include decimals for floats and leave them off for ints - we'll use the values
			# declared here to enforce types coming from settings.
			
			'WheelDia':23.5,		#diameter of the filament roller wheel
			'RotPositiveDir':'DirCCWPositive',
			'no_filament_gcode':'',
			'sensor_enabled': True,
			'SearchForSensor': True,
			'USBDevice':'/dev/ttyUSB0',
			'baudrate': 115200,
			'ArmAlarmDelay': 30,
			'alarmaction': 'pause',
			'ErrorOnDeviationmm': 20,
			'windowduration': 120,
			'driftCorrectionInterval':180,
			'CorrectDriftOnArm': True
		})
	
	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)		
		self.SettingsToSelf()
		
		
	def get_api_commands(self):
		return dict(
			ToggleArm=[],
			CorrectDriftNow=[]
		)

	def on_api_command(self, command, data):
		self._logger.info("Received OnAPICommand: " + str(command))
		if command == "ToggleArm":
		
			if self.ManuallyDisarmed:
				self.ManuallyDisarmed = False
				# set to now to force arm immediately
				self.ArmAlarmTime = time.time()
				self.FWLog("Manually ARMED.")
			else:
				self.ManuallyDisarmed = True
				self.armed = False
				self.ArmAlarmTime = 0
				self.FWLog("Manually DISARMED.")

		elif command == "CorrectDriftNow":
			self.ForceDriftCorrectionNow()
				

	def get_template_configs(self):
		return [dict(type="settings", custom_bindings=False)]

	def get_assets(self):
		return dict(
			js=['js/filamentwatch.js'],
			css=['css/filamentwatch.css']
		)

	def on_event(self, event, payload):
		if not self.sensor_enabled:
#			self._logger.info("rotart sensor not enabled, ignoring event.")
			return

		if event == Events.CONNECTED:
			if self.SearchForSensor:
				PrinterPort = []
				PrinterPort.append(payload["port"])
				self._logger.info("Printer connected on port " + payload["port"])
				FWPort = self.SearchForFilamentWatch(ExcludePorts = PrinterPort)
				if FWPort:
					self._settings.set(["USBDevice"], FWPort)
					
			
		if event == Events.PRINT_STARTED:
			self._logger.info("%s: Enabling filament sensor." % (event))

			self.ResetRotaryVars()

			self.setup_serial()
			if not self.sensor_enabled:
				return

			self.printing = True
			self.WaitForFirstMove = True
			self.gcode_forecast[int(time.time())] = 0
			self.ROT_Timer = octoprint.util.RepeatedTimer(1, self.ROT_Worker)

			self.FWLog("Print Started. Waiting for first move.")
			self.Send2ClientStarted()
			self.Send2ClientDataUpdate("Waiting for first move.")
			
			self.SendPNotify("Filement Watch", "Print started - Monitoring this print.", hide = True)

		elif event == Events.PRINT_RESUMED:
			self._logger.info("%s: Resetting filament sensor." % (event))
			# kick off the drift correction routine to set the measured filament length
			# to the current gcode length.
			self.ForceDriftCorrectionNow()
			self.alarm = False
			self.ArmAlarmTime = time.time() + self.ArmAlarmDelay
			self.PrintPaused = False

				
		# Disable sensor
		elif event in (
			Events.PRINT_DONE,
			Events.PRINT_FAILED,
			Events.PRINT_CANCELLED,
			Events.ERROR
		):
			if not self.printing:
				# We frequently get multiple events that indicate print is done,
				# but let's not annoy our users with multiple messages, so if we've
				# fired, let's not do it again.
				return
			
			self._logger.info("%s: Disabling filament sensor." % (event))
			
			self.printing=False
			self.close_serial()
			self.ROT_Timer.cancel()
			
			self.FWLog("Stopping monitor on Event %s" %(event))
			self.Send2ClientDataUpdate("Print Stopped.")

	def get_update_information(self):
		return dict(
			octoprint_filamentwatch=dict(
				displayName="Filament Watch",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="Gene Matocha",
				repo="Filament-Watch-Octoprint-Plugin",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/gmatocha/Filament-Watch-Octoprint-Plugin/archive/{target_version}.zip"
			)
		)
		
	def sent_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
#		self._logger.info("Sent Command: {cmd}".format(**locals()))
		
		#todo - we don't yet handle relative gcode at all. Need to fix that.
		#todo - we don't yet handle extrusion only commands at all. That's usually just for testing, but still want to add that.
		#todo - we don't yet handle arc moves (except to disable FW).
		
		if not self.sensor_enabled:
			self._logger.info("rotart sensor not enabled, ignoring event.")
			return
			
		if not gcode:
			return

		self._logger.info("Sent_gcode:" + str(cmd))

		if gcode in (
			"G2",
			"G3"
			):
			self.FWLog("G2/3: Filament Watch does not currently support Arc moves. Disabled.")
			self.Send2ClientDataUpdate("Arm move unsupported.")
			self._settings.set(["sensor_enabled"], False)
			self.close_serial()
			self.ROT_Timer.cancel()

		if gcode in (
			"G0",
			"G1"
			):
		
			CmdDict = dict ((cmd,float(val)) for discard,cmd,val in (self.GCODESplitter.split(OneCmd) for OneCmd in cmd.upper().split()))

			# Check if this is first move
			if self.WaitForFirstMove:
				self.WaitForFirstMove = False
				# clear the serial IO buffer
				self.RotaryEncoder.reset_input_buffer()
				self.ROT_Timer.start()

			# Get the feedrate
			if "F" in CmdDict:
				f = CmdDict["F"]
				# convert to mm per second
				f = f/60
				self.Feedrate = f
				self._logger.info("New Feedrate:" + str(self.Feedrate))

			# Get the extruded length
			if "E" in CmdDict:
				e = CmdDict["E"]

				e = e + self.ROT_ExtrudedLenBase
					 
				self.ExLen_gcode = round(e, 2)
					
				self._logger.info("New extruded length:" + str(self.ExLen_gcode))

			# get the x,y and determine if the move is a long one
			if "X" in CmdDict or "Y" in CmdDict:
				if "X" in CmdDict:
					x = CmdDict["X"]
				else:
					x = self.LastX
					
				if "Y" in CmdDict:
					y = CmdDict["Y"]
				else:
					y = self.LastY
				
				if self.LastX != -1 and self.LastY != -1 and self.Feedrate:
					# if we havent gotten real x and y, we can't do any of the math, so let's just store and skip the rest
					deltaX = abs(self.LastX - x)
					deltaY = abs(self.LastY - y)
					now = int(time.time())
				
					moveDist = math.sqrt(deltaX ** 2 + deltaY ** 2)
					# moveDuration is how long the move is estimated to make in whole seconds
					moveDuration = int(moveDist / self.Feedrate);

					self._logger.info("Forecasting vars moveDuration " + str(moveDuration) + " MoveDist " + str(moveDist))
					
					# get the last time in the gcode forecast, or now, whichever is greater
					lastTime = next(reversed(self.gcode_forecast))
					lastLen = self.gcode_forecast[lastTime]
					if lastTime > now:
						self._logger.info("Forecasting - this move is " + str(lastTime - now) + " seconds in future")
						now = lastTime
					
					if not moveDuration:
						self.gcode_forecast[now] = self.ExLen_gcode
						self._logger.info("Forecasting - this is a zero time move. E= " + str(self.ExLen_gcode) + " at " + str(now))
					else:
						mmPerSec = (self.ExLen_gcode - self.LastE) / moveDuration
						for i in range(moveDuration):
							t = now + i
							newE = lastLen + ((i+1) * mmPerSec)
							self.gcode_forecast[t] = newE
							
							self._logger.info("Forecasting future extrusions:" + str(newE) + " at " + str(t))
					
				self.LastX = x
				self.LastY = y
				self.LastE = self.ExLen_gcode
					
			
			if "Z" in CmdDict: 
				self.LastKnownZ = CmdDict["Z"]

		# Reset Filament Length
		if gcode == "G92":
			CmdDict = dict ((x,float(y)) for d,x,y in (self.GCODESplitter.split(OneCmd) for OneCmd in cmd.upper().split()))
			if "E" in CmdDict:
				e = CmdDict["E"]
	
				# why subtract e? e is almost always 0 on a reset. But just in case it's set to some positive
				# value, that's a forced value, not actual extruded length. Future extrusions
				# will include that arbitrary value, so we need to take it out.
				e = self.ExLen_gcode - e
				self.ROT_ExtrudedLenBase = round(e, 2)
				self.FWLog("G92: set extruded base:" + str(self.ROT_ExtrudedLenBase))


def __plugin_load__():
	global __plugin_name__
	__plugin_name__ = "Filament Watch"
	
	global __plugin_version__
	__plugin_version__ = "0.9.0"
	
	global __plugin_implementation__
	__plugin_implementation__ = filamentwatchPlugin()
	
	global __plugin_helpers__
	__plugin_helpers__ = dict(
		FilamentWatchExtrudedInfo = filamentwatchPlugin.InfoHelper
	)

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.sent_gcode
	}
