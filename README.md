# Klipper Filament Dryer

## ** CURRENTLY IN BETA **

## Introduction

Klipper add-on to turn on a filament dryer heater based on the humidity level. A GCode command is also provided to dry the filament on demand for xx minutes.

## Sample Config

<pre>[filament_dryer filament_dryer]
interval: 1
sensor: dryer_sensor
heater: dryer_heater
target_humidity: 30
target_temp: 60
default_manual_dry_time: 45
auto_dry_time: 30</pre>

## Requirements

- Humidity/Temperature Sensor such as BME280/680
- Heater

## Additional Config Needed

The following configs are also required for the heater and temperature sensor:

<pre>[heater_generic dryer_heater]
heater_pin: dryer:gpio6
sensor_type: temperature_combined
sensor_list: temperature_sensor dryer_sensor
maximum_deviation: 999
combination_method: min
control: watermark
max_delta: 3.0
min_temp: 0
max_temp: 100

[temperature_sensor dryer_sensor]
sensor_type: BME280
i2c_bus: i2c3_PB3_PB4
i2c_address: 119

[heater_fan dryer_fan]
pin: dryer:gpio14
max_power: 0.5
off_below: 0.31
heater: dryer_heater
heater_temp: 25
shutdown_speed: 0</pre>

The BME280 config above will depend on the MCU you're using. Please refer to the [Klipper Config Reference](https://www.klipper3d.org/Config_Reference.html#bmp180bmp280bme280bme680-temperature-sensor) or [Klipper Discord](https://discord.klipper3d.org/) for help on configuring this sensor.

Note that a heater_fan is added to ensure the fan turns on with the heater and turns off when the dryer chamber temp is below a certain threshold (in this case, 25 degrees). Max_power should also be adjusted to your needs. If using more than 1 fan, consider configuring these as [multi_pin](https://www.klipper3d.org/Config_Reference.html#multi_pin):

<pre>[multi_pin multi_dryer_fans]
pins: dryer:gpio14,dryer:gpio13

[heater_fan dryer_fans]
pin: multi_pin:multi_dryer_fans
max_power: 0.5
off_below: 0.31
heater: dryer_heater
heater_temp: 25
shutdown_speed: 0</pre>

## Install

<pre>cd ~
git clone https://github.com/Turge08/klipper_filament_dryer
cd klipper_filament_dryer
./install.sh</pre>

## Removal

<pre>cd ~
sudo rm -r ~/klipper_filament_dryer
sudo rm -r ~/klipper/klippy/extras/filament_dryer.py</pre>

## Settings

- **interval**: How often to check the humidity level
- **sensor**: Sensor name of the humidity/temperature sensor
- **heater**: heater to control
- **target_humidity**: Target humidity. If humidity is above the target, the heater will be enabled. Once the humidity is below the target, the heater is turned off
- **target_temp**: Temperature the heater will be set to when enabled
- **default_manual_dry_time**: When manually enabling the dryer, the heater will be enabled for this amount of minutes unless specified otherwise
- **auto_dry_time**: When automatically enabling the dryer based on the humidity, setting this value to non-zero will force the dryer to remain enabled for this amount of minutes

## Manual Filament Drying

The dryer can be manually enabled for the default dry time by running the following gcode command: DRY_FILAMENT
To dry the filament for a custom time: DRY_FILAMENT MINUTES=120

Alternatively, add this macro to printer.cfg to manually enable the dryer from Fluidd or Mainsail:

<pre>[gcode_macro DRY_FILAMENT]
rename_existing: BASE_DRY_FILAMENT
gcode:
    {% if 'MINUTES' in params %}
        BASE_DRY_FILAMENT MINUTES={params.MINUTES}
    {% else %}
        BASE_DRY_FILAMENT
    {% endif %}</pre>

![image](https://github.com/Turge08/klipper_filament_dryer/assets/6312320/d6d41c2f-8a88-4147-98a0-ef559735fbcd)

## Misc

Running the GCode command "GET_FILAMENT_DRYER_INFO" will return information about the dryer including the time remaining if the heater is enabled:

<pre>// Humidity: 26
// Temperature: 23
// Target Temp: 60
// Dry Mode: Manual
// Dry Time Left: 0:00:57</pre>


