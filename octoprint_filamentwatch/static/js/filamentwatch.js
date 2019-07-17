/*jslint browser: true, devel: true*/

$(function() {
	
	function FilamenentWatchViewModel(parameters) {
        self = this;

		self.controlViewModel = parameters[0];
		self.loginStateViewModel = parameters[1];
		
		self.gcode = 0.0
		self.gcode_forecast = 0.0
		self.actual = 0.0
		
		self.TargetRangeLo = []
		self.TargetRangeHi = []
		self.gcode_history = []
		self.actual_history = []
		self.gcode_forecast_graphdata = []
		self.gcode_forecast_past = []
		
		self.WindowLen = 120
		self.GraphRangeHi = 10
		self.GraphRangeLo = 0
		self.Armed = false
		
		self.LastNow = 0
		
		self.ClientSideArmed = ko.observable()
		self.ClientSidePrinting = ko.observable()
		self.SearchForSensor = ko.observable()
		
		self.SetupGraph = function(force)
		{
			if (OctoPrint.coreui.selectedTab !== "#tab_plugin_filamentwatch" ||
				!$("#tab_plugin_filamentwatch").is(":visible")) {
				// do not try to initialize the graph when it's not visible or its sizing will be off
				console.log("Not initializeing extrudded len graph because not visible")
				
				return;
			}


		// AEM - this is mostly copied from Octoprint temp-graph code
		//-------------------		
			var graph = $("#extrudedLength-graph");
			if (!graph.length) return; // no graph
		//	if (self.plot && !force) return; // already initialized

			var options = {
				yaxis: {
					min: self.GraphRangeLo,
					max: self.GraphRangeHi,
					ticks: 10,
					tickFormatter: function(val, axis) {
						if (val === undefined || val === 0)
							return "";
						return val + " mm";
					}
				},
				xaxis: {
					mode: "time",
					minTickSize: [15, "second"],
					min: Date.now() - (self.WindowLen * 1000),
					tickFormatter: function(val, axis) {
						if (val === undefined || val === 0)
							return ""; // we don't want to display the minutes since the epoch if not connected yet ;)

						// current time in milliseconds in UTC
						var timestampUtc = Date.now();

						// calculate difference in milliseconds
						var diff = timestampUtc - val;

						// convert to seconds
						var diffInSec = Math.round(diff / 1000);
						if (diffInSec === 0)
						{
							return "Now";
						}
						else if (diffInSec < 0)
						{
							return "+ " + diffInSec + " " + gettext("sec");
						}
						else
						{
							return "- " + diffInSec + " " + gettext("sec");
						}
					}
				},
				legend: {
					position: "sw",
					noColumns: 4,
					backgroundOpacity: 0
				}
			};
			
			if (!OctoPrint.coreui.browser.mobile) {
				options["crosshair"] = { mode: "x" };
				options["grid"] = { hoverable: true, autoHighlight: false };
			}
			
			// Flot 0.8.3 doesn't do fillBetween properly, so I'll fill below the low bound with white
			// fillBetween is fixed in later versions - when that's picked up by OP, the color below should match the high bound color
			// and the graph will look better.
			var LowAlarmBound =	{ id: "LowBound", data: self.TargetRangeLo, lines: { show: true, lineWidth: 0.1}, color: "rgb(50,255,50)" }
			if ($.plot.version == '0.8.3')
				LowAlarmBound =	{ id: "LowBound", data: self.TargetRangeLo, lines: { show: true, lineWidth: 0.1, fill: 1 }, color: "rgb(255,255,255)" }

			var dataset = [
				{ label: "Alarm Boundry", id: "HighBound", data: self.TargetRangeHi, lines: { show: true, lineWidth: 0.1, fill: 0.2 }, color: "rgb(50,255,50)", fillBetween: "LowBound" },
				LowAlarmBound,
				{ label: "GCode Commanded", data: self.gcode_history, lines: { show: true, lineWidth: 1 }, color: "rgb(50,50,50)" },
				{ label: "Measured Len", data: self.actual_history, lines: { show: true, lineWidth: 1 }, color: "rgb(100,100,255)"  },
				{ label: "GCode Forecast", data: self.gcode_forecast_graphdata, lines: { show: true, lineWidth: 1 }, color: "rgb(255,242,0)"  }
			];

			self.plot = $.plot(graph, dataset, options);
		};
		
		self.onAfterTabChange = function (current, previous)
		{
			if (current === "#tab_plugin_filamentwatch" && self.loginStateViewModel.isUser())
			{
				self.SetupGraph();
				return;
			}
		};


        // This will get called before the View Model gets bound to the DOM, but after its
        // dependencies have already been initialized. It is especially guaranteed that this method
        // gets called _after_ the settings have been retrieved from the OctoPrint backend and thus
        // the SettingsViewModel been properly populated.
        self.onBeforeBinding = function() {
        }


		self.ToggleArmDisarm = function()
		{
		   $.ajax({
					url: API_BASEURL + "plugin/filamentwatch",
					type: "POST",
					dataType: "json",
					contentType: "application/json; charset=UTF-8",
					data: JSON.stringify({command: "ToggleArm"})
				})
		}
		
		self.CorrectDriftNow = function()
		{
		   $.ajax({
					url: API_BASEURL + "plugin/filamentwatch",
					type: "POST",
					dataType: "json",
					contentType: "application/json; charset=UTF-8",
					data: JSON.stringify({command: "CorrectDriftNow"})
				})
		}
		
		self.onDataUpdaterPluginMessage = function (plugin, datadict)
		{
			if (plugin !== "filamentwatch")
			{
				return;
			}
			
			if (datadict.type == "PNotify")
			{
				console.log("Poping PNotify");
				var data = datadict.data;
				
				new PNotify({
						title: data.title,
						text: data.text,
						type: data.type,
						hide: data.hide
						});	
	
				return;
			}
			if (datadict.type == "Starting")
			{
				// Just clear out any old data that might be there
				self.TargetRangeLo.length = 0
				self.TargetRangeHi.length = 0
				self.gcode_history.length = 0
				self.actual_history.length = 0
				self.gcode_forecast_graphdata.length = 0
				self.gcode_forecast_past.length = 0
				self.gcode = 0.0
				self.gcode_forecast = 0.0
				self.actual = 0.0
			
				return;
			}
			else if (datadict.type == "filament_data")
			{
				var filament_data = datadict.data;
			}
			else
			{
				console.log("Unrecognized data type " + data.type);
				return;
			}
			
			var deltat = (Date.now() - self.LastNow) / 1000
			self.LastNow = Date.now();
			
			self.WindowLen = filament_data.history_length;
			var gcodeRate = (parseFloat(filament_data.gcode) - self.gcode) / deltat;
			self.gcode =  parseFloat(filament_data.gcode);
			var gcode_forecastRate = (parseFloat(filament_data.gcode_forecast) - self.gcode_forecast) / deltat;
			self.gcode_forecast =  parseFloat(filament_data.gcode_forecast);
			var actualRate = (parseFloat(filament_data.actual) - self.actual) / deltat;
			self.actual =  parseFloat(filament_data.actual);
			var ErrorOnDeviationmm = parseFloat(filament_data.ErrorOnDeviationmm);
			var time = filament_data.time;
			
			var RangeHi = self.gcode_forecast + ErrorOnDeviationmm;
			var RangeLo = self.gcode_forecast - ErrorOnDeviationmm;
			RangeLo = RangeLo < 0 ? 0 : RangeLo;

			self.TargetRangeLo.push([time, RangeLo]);
			self.TargetRangeHi.push([time, RangeHi]);
			self.gcode_history.push([time, self.gcode]);
			self.actual_history.push([time, self.actual]);
			self.gcode_forecast_past.push([time, self.gcode_forecast]);
			
			// Ok this is confusing.
			// gcode_forecast_graphdata is the graph data for the forecasted (calculated) extrusions
			// it contains a 120 second window of the past extrusions, which are maintained
			// here - for efficiency they are not set from the server side as a block - they are sent one 
			// at a time and the history is maintained on this side.
			// But the server does send all the FUTURE gcode forecasts in a single block
			// so here we put the two together to make a continuous graph that goes 
			// into the past and future.
			self.gcode_forecast_graphdata = self.gcode_forecast_past;
			gfp = filament_data.gcode_forecast_predictions

			// convert to ms
			gfp.forEach(function(element) {
				element[0] = element[0] * 1000
				console.log(element);
			});
			self.gcode_forecast_graphdata = self.gcode_forecast_graphdata.concat(gfp);
			
			// Trim evrything to length...not sure if this is more or less efficient than slice
			while (self.TargetRangeHi.length > self.WindowLen)
				self.TargetRangeHi.shift();
			
			while (self.TargetRangeLo.length > self.WindowLen)
				self.TargetRangeLo.shift();

			while (self.gcode_history.length > self.WindowLen)
				self.gcode_history.shift();
			
			while (self.actual_history.length > self.WindowLen)
				self.actual_history.shift();
			
			while (self.gcode_forecast_graphdata.length > self.WindowLen)
				self.gcode_forecast_graphdata.shift();
			
			
			try
			{
				self.GraphRangeHi = Math.max(self.gcode, RangeHi, self.actual) + 10;
				self.GraphRangeLo = Math.min(self.TargetRangeLo[0][1], self.gcode_forecast_graphdata[0][1], self.actual_history[0][1]) - 10;
//				self.GraphRangeLo = self.GraphRangeLo < 0 ? 0 : self.GraphRangeLo;
			}
			catch(err)
			{
				console.log("FilamentWatch: history data error " + String(err));
			}

			var ArmedText = "Yes";
			if (!filament_data.armed)
			{
				var ArmedText = "No";
				// Manually Disabled is the only condition that can leave us armed
				// and with a zero alarm countdown
				if (filament_data.arm_alarm_in_sec)
					ArmedText = 'In ' + String(filament_data.arm_alarm_in_sec) + ' sec';
				if (filament_data.ManuallyDisarmed)
					ArmedText = 'Manually Disabled';
			}

			// calulated valies for display purposes
			var FilamentError = self.actual - self.gcode_forecast;

			$('#printing').html(filament_data.printing ? 'Yes' : 'No');
			$('#alarm').html(filament_data.alarm ? 'Yes' : 'No');
			$('#armed').html(ArmedText);
			$('#summary').html(filament_data.summary);
			$('#gcode_forecast_pos').html(self.gcode_forecast.toFixed(2) + " mm / " + gcode_forecastRate.toFixed(2) + " mm/s");
			$('#measured_pos').html(self.actual.toFixed(2) + " mm / " + actualRate.toFixed(2) + " mm/s");
			$('#gcode_pos').html(self.gcode.toFixed(2) + " mm / " + gcodeRate.toFixed(2) + " mm/s");
			$('#allowed_deviation').html(ErrorOnDeviationmm.toFixed(2) + " mm (" + FilamentError.toFixed(2) + " mm)");
			$('#log_msgs').html(filament_data.log_msgs);
			$('#feed_rate').html(filament_data.FeedRate.toFixed(2) + " mm/s");
			
			self.ClientSideArmed(filament_data.armed);
			self.ClientSidePrinting(filament_data.printing);
			
			self.SetupGraph();
		}
		
    }
		
	
    // This is how our plugin registers itself with the application, by adding some configuration
    // information to the global variable OCTOPRINT_VIEWMODELS
    OCTOPRINT_VIEWMODELS.push([
        // This is the constructor to call for instantiating the plugin
        FilamenentWatchViewModel,

        // This is a list of dependencies to inject into the plugin, the order which you request
        // here is the order in which the dependencies will be injected into your view model upon
        // instantiation via the parameters argument

//        ["settingsViewModel", "controlViewModel", "loginStateViewModel"],
        ["controlViewModel", "loginStateViewModel"],

        // Finally, this is the list of selectors for all elements we want this view model to be bound to.
        ["#tab_plugin_filamentwatch"]
//        ["#settings_plugin_filamentwatch", "#tab_plugin_filamentwatch", "#wizard_plugin_filamentwatch"]
    ]);
	
	
	
});
