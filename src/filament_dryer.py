class filament_dryer:
    def __init__(self, config):
        self.name = config.get_name().split()[-1]
        self.printer = config.get_printer()
        self.interval = config.getint('interval',1,1,60)
        self.sensor_name = config.get('sensor')
        reactor = self.printer.get_reactor()
        self.dry_target_time = reactor.monotonic()
        self.heater_name = config.get('heater')
        self.target_temp = config.getint('target_temp', 60, 20, 100)
        self.default_dry_time = config.getint('default_dry_time', 60, 10, 600)
        self.target_humidity = config.getint('target_humidity', 30, 10, 100)
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command("GET_FILAMENT_DRYER_INFO",
            self.cmd_GET_FILAMENT_DRYER_INFO,
            desc=self.cmd_GET_FILAMENT_DRYER_INFO_help)
        self.gcode.register_command("DRY_FILAMENT",
            self.cmd_DRY_FILAMENT,
            desc=self.cmd_DRY_FILAMENT_help)
        self.printer.register_event_handler("klippy:connect", self.handle_connect)
        self.printer.register_event_handler("klippy:ready", self.handle_ready)

    def callback(self, eventtime):
        reactor = self.printer.get_reactor()
        if reactor.monotonic() > self.dry_target_time or self.heater.target_temp == 0:
            self.dry_target_time = reactor.monotonic()
            if self.sensor.humidity > self.target_humidity:
                if self.heater.target_temp == 0:
                    self.gcode.respond_info("Turning on heater")
                    self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=%i" % (self.heater_name, self.target_temp))
            else:
                if self.heater.target_temp != 0:
                    self.gcode.respond_info("Turning off heater")
                    self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=0" % (self.heater_name))
        return eventtime + self.interval

    def handle_connect(self):
        self.heater = self.printer.lookup_object('heater_generic ' + self.heater_name)
        self.sensor = self.printer.lookup_object('bme280 ' + self.sensor_name)

    def handle_ready(self):
        reactor = self.printer.get_reactor()
        reactor.register_timer(self.callback, reactor.monotonic()+self.interval)
        self.gcode.respond_info("Callback Initialized")

    cmd_GET_FILAMENT_DRYER_INFO_help = "Get Filament Dryer Info"
    def cmd_GET_FILAMENT_DRYER_INFO(self, gcmd):
        self.gcode.respond_info("Humidity: %i" % (self.sensor.humidity))
        self.gcode.respond_info("Temperature: %i" % (self.sensor.temp))
        self.gcode.respond_info("Target Temp: %i" % (self.heater.target_temp))

    cmd_DRY_FILAMENT_help = "Dries filament for XX minutes"
    def cmd_DRY_FILAMENT(self, gcmd):
        self.dry_time = gcmd.get_int('MINUTES', self.default_dry_time, minval=1, maxval=600)
        self.gcode.respond_info("Drying filament for %i minutes" % (self.dry_time))
        reactor = self.printer.get_reactor()
        self.dry_target_time = reactor.monotonic() + self.dry_time * 60
        self.gcode.run_script_from_command("SET_HEATER_TEMPERATURE HEATER=%s TARGET=%i" % (self.heater_name, self.target_temp))

    def get_status(self, eventtime):
        return {
            'name': self.name,
            'info': "{'target_humidity': '%f', 'interval': '%i'}" % (self.target_humidity, self.interval),
            'data': "{'humidity': '%i', 'temperature': '%i'}" % (self.sensor.humidity, self.sensor.temp)
        }

def load_config_prefix(config):
    return filament_dryer(config)
