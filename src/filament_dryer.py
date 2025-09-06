from datetime import timedelta

class filament_dryer:
    def __init__(self, config):
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        self.interval = config.getint('interval',1,1,60)
        self.sensor_name = config.get('sensor')
        reactor = self.printer.get_reactor()
        self.dry_target_time = reactor.monotonic()
        self.vent_target_time = reactor.monotonic()
        self.dry_mode = "Off"
        self.heater_name = config.get('heater')
        self.auto_target_temp = config.getint('auto_target_temp', 60, 20, 100)
        self.manual_target_temp = config.getint('manual_target_temp', 60, 20, 100)
        self.default_manual_dry_time = config.getint('default_manual_dry_time', 60, 1, 600)
        self.auto_dry_time = config.getint('auto_dry_time', 0, 0, 600)
        self.target_humidity = config.getint('target_humidity', 30, 2, 100)
        self.dryer_enabled = True
        self.manual_dryer_on_macro = config.get('manual_dryer_on_macro', '')
        self.auto_dryer_on_macro = config.get('auto_dryer_on_macro', '')
        self.dryer_off_macro = config.get('dryer_off_macro', '')
        self.vent_interval = config.getint('vent_interval', 0, 0, 600)
        self.vent_length = config.getint('vent_length', 0, 0, 600)
        self.vent_start_macro = config.get('vent_start_macro', '')
        self.vent_end_macro = config.get('vent_end_macro', '')
        self.vent_mode = "Off"
        if self.vent_interval == 0:
            self.vent_mode = "Disabled"
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command("GET_FILAMENT_DRYER_INFO",
            self.cmd_GET_FILAMENT_DRYER_INFO,
            desc=self.cmd_GET_FILAMENT_DRYER_INFO_help)
        self.gcode.register_command("DRY_FILAMENT",
            self.cmd_DRY_FILAMENT,
            desc=self.cmd_DRY_FILAMENT_help)
        self.gcode.register_command("STOP_FILAMENT_DRYER",
            self.cmd_STOP_FILAMENT_DRYER,
            desc=self.cmd_STOP_FILAMENT_DRYER_help)
        self.gcode.register_command("DISABLE_FILAMENT_DRYER",
            self.cmd_DISABLE_FILAMENT_DRYER,
            desc=self.cmd_DISABLE_FILAMENT_DRYER_help)
        self.gcode.register_command("ENABLE_FILAMENT_DRYER",
            self.cmd_ENABLE_FILAMENT_DRYER,
            desc=self.cmd_ENABLE_FILAMENT_DRYER_help)
        self.printer.register_event_handler("klippy:connect",
            self.handle_connect)
        self.printer.register_event_handler("klippy:ready",
            self.handle_ready)

    def venting_callback(self, eventtime):
        reactor = self.printer.get_reactor()
        if self.vent_mode == "Off":
            return eventtime + self.interval
        if self.heater.target_temp == 0 and self.vent_mode != "Off":
            if self.vent_end_macro and self.vent_mode == "Open":
                self.gcode.respond_info("Executing %s" % (self.vent_end_macro))
                self.gcode.run_script_from_command(self.vent_end_macro)
            self.vent_target_time = reactor.monotonic()
            self.vent_mode = "Off"
            return eventtime + self.interval
        if reactor.monotonic() > self.vent_target_time and self.vent_mode == "Open":
            self.vent_mode = "Closed"
            if self.vent_end_macro:
                self.gcode.respond_info("Executing %s" % (self.vent_end_macro))
                self.gcode.run_script_from_command(self.vent_end_macro)
            self.vent_target_time = reactor.monotonic() + self.vent_interval * 60
        elif reactor.monotonic() > self.vent_target_time and self.vent_mode == "Closed":
            self.vent_mode = "Open"
            if self.vent_start_macro:
                self.gcode.respond_info("Executing %s" % (self.vent_start_macro))
                self.gcode.run_script_from_command(self.vent_start_macro)
            self.vent_target_time = reactor.monotonic() + self.vent_length
        return eventtime + self.interval

    def callback(self, eventtime):
        reactor = self.printer.get_reactor()
        if self.heater.target_temp == 0 and self.dry_mode != "Off":
            self.dry_mode = "Off"
            if self.dryer_off_macro:
                self.gcode.respond_info("Executing %s" % (self.dryer_off_macro))
                self.gcode.run_script_from_command(self.dryer_off_macro)
        if reactor.monotonic() > self.dry_target_time or self.heater.target_temp == 0:
            if self.sensor.humidity > self.target_humidity and self.dryer_enabled:
                if self.heater.target_temp == 0:
                    self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=%i" % (self.heater_name, self.auto_target_temp))
                    self.dry_mode = "Auto"
                    if self.auto_dry_time > 0:
                        self.gcode.respond_info("Current humidity: %i, Target humidity: %i. Turning on heater for %i minutes" % (self.sensor.humidity, self.target_humidity, self.auto_dry_time))
                        self.dry_target_time = reactor.monotonic() + self.auto_dry_time * 60
                    else:
                        self.gcode.respond_info("Current humidity: %i, Target humidity: %i. Turning on heater" % (self.sensor.humidity, self.target_humidity))
                        self.dry_target_time = reactor.monotonic()
                    if self.vent_interval > 0:
                        self.vent_target_time = reactor.monotonic() + self.vent_interval * 60
                        self.vent_mode = "Closed"
                    if self.auto_dryer_on_macro:
                        self.gcode.respond_info("Executing %s" % (self.auto_dryer_on_macro))
                        self.gcode.run_script_from_command(self.auto_dryer_on_macro)
            else:
                if self.dry_mode != "Off" and self.heater.target_temp != 0:
                    self.gcode.respond_info("Current humidity: %i, Target humidity: %i. Turning off heater." % (self.sensor.humidity, self.target_humidity))
                    self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=0" % (self.heater_name))
        return eventtime + self.interval

    def handle_connect(self):
        try:
            self.heater = self.printer.lookup_object('heater_generic ' + self.heater_name)
        except Exception:
            raise self.printer.config_error("Could not find 'heater_generic [%s]' heater definition" % (self.heater_name))
        try:
            self.sensor = self.printer.lookup_object('bme280 ' + self.sensor_name)
        except Exception:
            raise self.printer.config_error("Could not find 'bme280 [%s]' sensor definition" % (self.sensor_name))

    def handle_ready(self):
        reactor = self.printer.get_reactor()
        reactor.register_timer(self.callback, reactor.monotonic() + self.interval)
        if self.vent_interval > 0:
            reactor.register_timer(self.venting_callback, reactor.monotonic() + self.interval)
        if self.auto_target_temp > self.heater.max_temp - 2:
            raise self.printer.config_error("auto_target_temp of %s needs to be at least 2 degrees below heater max temp of %s" % (self.auto_target_temp, self.heater.max_temp))
        if self.manual_target_temp > self.heater.max_temp - 2:
            raise self.printer.config_error("manual_target_temp of %s needs to be at least 2 degrees below heater max temp of %s" % (self.manual_target_temp, self.heater.max_temp))
        self.gcode.respond_info("Max Heater Temp: %f" % (self.heater.max_temp))

    cmd_GET_FILAMENT_DRYER_INFO_help = "Get Filament Dryer Info"
    def cmd_GET_FILAMENT_DRYER_INFO(self, gcmd):
        self.gcode.respond_info("Humidity: %i" % (self.sensor.humidity))
        self.gcode.respond_info("Temperature: %i" % (self.sensor.temp))
        self.gcode.respond_info("Target Temp: %i" % (self.heater.target_temp))
        self.gcode.respond_info("Dry Mode: %s" % (self.dry_mode))
        seconds = self.dry_target_time - self.printer.get_reactor().monotonic()
        if self.dry_mode == "Off":
            seconds = 0
        mm, ss = divmod(seconds, 60)
        hh, mm = divmod(mm, 60)
        self.gcode.respond_info("Dry Time Left: %i:%02i:%02i" % (hh,mm,ss))

        self.gcode.respond_info("Vent Mode: %s" % (self.vent_mode))
        seconds = self.vent_target_time - self.printer.get_reactor().monotonic()
        if self.vent_mode == "Off":
            seconds = 0
        if self.vent_mode != "Disabled":
            mm, ss = divmod(seconds, 60)
            hh, mm = divmod(mm, 60)
            self.gcode.respond_info("Vent Time Left: %i:%02i:%02i" % (hh,mm,ss))

    cmd_DRY_FILAMENT_help = "Dries filament for XX minutes"
    def cmd_DRY_FILAMENT(self, gcmd):
        self.dry_time = gcmd.get_int('MINUTES', self.default_manual_dry_time, minval=0, maxval=600)
        target_temp = gcmd.get_int('TEMP', self.manual_target_temp, minval=20, maxval=100)
        if target_temp > self.heater.max_temp - 2:
            self.gcode.respond_info("target_temp of %s needs to be at least 2 degrees below heater max temp of %s" % (target_temp, self.heater.max_temp))
            return
        reactor = self.printer.get_reactor()
        self.dry_target_time = reactor.monotonic() + self.dry_time * 60
        if self.vent_interval > 0:
            self.vent_target_time = reactor.monotonic() + self.vent_interval * 60
            self.vent_mode = "Closed"
        if self.dry_time == 0:
            self.gcode.respond_info("Turning off manual drying")
        else:
            self.gcode.respond_info("Drying filament for %i minutes" % (self.dry_time))
            self.dry_mode = "Manual"
            self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=%i" % (self.heater_name, target_temp))
            if self.manual_dryer_on_macro:
                self.gcode.respond_info("Executing %s" % (self.manual_dryer_on_macro))
                self.gcode.run_script_from_command(self.manual_dryer_on_macro)

    cmd_DISABLE_FILAMENT_DRYER_help = "Disables automatic filament dryer"
    def cmd_DISABLE_FILAMENT_DRYER(self, gcmd):
        self.gcode.respond_info("Disabling automatic filament dryer")
        self.dryer_enabled = False
        self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=0" % (self.heater_name))

    cmd_ENABLE_FILAMENT_DRYER_help = "Enabled automatic filament dryer"
    def cmd_ENABLE_FILAMENT_DRYER(self, gcmd):
        self.gcode.respond_info("Enabling automatic filament dryer")
        self.dryer_enabled = True

    cmd_STOP_FILAMENT_DRYER_help = "Stops filament dryer heater"
    def cmd_STOP_FILAMENT_DRYER(self, gcmd):
        self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=0" % (self.heater_name))

    def get_status(self, eventtime):
        try:
            seconds = self.dry_target_time - self.printer.get_reactor().monotonic()
            if self.dry_mode == "Off":
                seconds = 0
            mm, ss = divmod(seconds, 60)
            hh, mm = divmod(mm, 60)
            return {
                'name': self.name,
                'config': "{'target_humidity': '%f', 'interval': '%i'}" % (self.target_humidity, self.interval),
                'info': "{'humidity': '%i', 'temperature': '%i', 'dry_mode': '%s', 'dry_time': '%i:%02i:%02i'}" % (self.sensor.humidity, self.sensor.temp, self.dry_mode, hh, mm, ss)
            }
        except Exception:
            return { }

def load_config_prefix(config):
    return filament_dryer(config)

