# Klipper Filament Dryer

## ** CURRENTLY IN BETA **

## Introduction

Klipper add-on to automatically turn on a filament dryer heater based on the humidity level or manually for a specified amount of time. An optional can also be opened/closed on an interval.

## Sample Config

<pre>[filament_dryer filament_dryer]
interval: 1
sensor: dryer_sensor
heater: dryer_heater
target_humidity: 30
auto_target_temp: 60
manual_target_temp: 80
default_manual_dry_time: 45
auto_dry_time: 30
manual_dryer_on_macro: MANUAL_DRYER_ON_MACRO
auto_dryer_on_macro: AUTO_DRYER_ON_MACRO
dryer_off_macro: DRYER_OFF_MACRO
vent_interval: 2
vent_length: 3
vent_start_macro: OPEN_VENT
vent_end_macro: CLOSE_VENT</pre>

## Requirements

- Humidity/Temperature Sensor such as BME280/680
- Heater
- Vent (optional)

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
- **auto_target_temp**: Temperature the heater will be set to when automatically enabled
- **manual_target_temp**: Temperature the heater will be set to when manually enabled
- **default_manual_dry_time**: When manually enabling the dryer, the heater will be enabled for this amount of minutes unless specified otherwise
- **auto_dry_time**: When automatically enabling the dryer based on the humidity, setting this value to non-zero will force the dryer to remain enabled for this amount of minutes
- **manual_dryer_on_macro**: name of macro to execute when heater is manually enabled
- **auto_dryer_on_macro**: name of macro to execute when heater is manually enabled
- **dryer_off_macro**:  name of macro to execute when heater is disabled
- **vent_interval**: interval in minutes to execute the vent open macro (see vent_start_macro)
- **vent_length**: length of time in seconds before executing the vent close macro (see vent_end_macro)
- **vent_start_macro**: name of macro to execute to open the vent
- **vent_end_macro**:  name of macro to execute to close the vent

## Manual Filament Drying

The dryer can be manually enabled for the default dry time and temperature by running the following gcode command: DRY_FILAMENT
To dry the filament for a custom time and temperature: DRY_FILAMENT MINUTES=120 TEMP=80

Alternatively, you can add this macro to printer.cfg to have it show up in your list of Macros in Fluidd/Mainsail:

<pre>[gcode_macro DRY_FILAMENT]
rename_existing: BASE_DRY_FILAMENT
gcode:
    {% set minutes = params.MINUTES | default(60) %}
    {% set temp = params.TEMP | default(70) %}
    BASE_DRY_FILAMENT MINUTES={minutes} TEMP={temp}</pre>

![image](https://github.com/Turge08/klipper_filament_dryer/assets/6312320/969f4eec-ba11-4fab-a9bb-ace189d2fd9f)

To stop the filament dryer, you can execute STOP_FILAMENT_DRYER or use the following macro:

<pre>[gcode_macro STOP_FILAMENT_DRYER]
rename_existing: BASE_STOP_FILAMENT_DRYER
gcode:
    BASE_STOP_FILAMENT_DRYER</pre>

## Misc

Running the GCode command "GET_FILAMENT_DRYER_INFO" will return information about the dryer including the time remaining if the heater is enabled:

<pre>// Humidity: 26
// Temperature: 23
// Target Temp: 60
// Dry Mode: Manual
// Dry Time Left: 0:00:57</pre>

## Example

My test filament dryer includes all controlled by a BTT EBB42 can bus toolhead PCB as the "dryer" mcu:

- a 24V 300W heater with a 24V fan
- a BME280 temperature and humidity sensor
- an iris vent controlled with a FS90R servo with another 24V fan

Full config:

<pre>[filament_dryer filament_dryer]
interval: 1
sensor: dryer_sensor
heater: dryer_heater 
target_humidity: 30
auto_target_temp: 60
manual_target_temp: 70
default_manual_dry_time: 120
auto_dry_time: 0
#manual_dryer_on_macro: MANUAL_DRYER_ON_MACRO
#auto_dryer_on_macro: AUTO_DRYER_ON_MACRO
#dryer_off_macro: DRYER_OFF_MACRO
vent_interval: 30
vent_length: 5
vent_start_macro: OPEN_VENT
vent_end_macro: CLOSE_VENT

[servo dryer_vent]
pin: dryer:PB9
initial_angle: 180
maximum_servo_angle: 250

[heater_fan dryer_fan]
pin: dryer:PA1
max_power: 0.5
off_below: 0.31
heater: dryer_heater
heater_temp: 25
shutdown_speed: 0

[fan_generic vent_fan]
pin: dryer:PA0
max_power: 1

[heater_generic dryer_heater]
heater_pin: dryer:PA2
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
i2c_mcu: dryer

[gcode_macro OPEN_VENT]
gcode:
    #SET_SERVO SERVO=dryer_vent ANGLE=270
    SET_FAN_SPEED FAN=vent_fan SPEED=1
    SET_SERVO SERVO=dryer_vent ANGLE=130
    G4 P{params.DELAY|default(900)}
    SET_SERVO SERVO=dryer_vent ANGLE=180
    SET_SERVO SERVO=dryer_vent WIDTH=0

[gcode_macro CLOSE_VENT]
gcode:
    #SET_SERVO SERVO=dryer_vent ANGLE=270
    SET_SERVO SERVO=dryer_vent ANGLE=230
    G4 P{params.DELAY|default(900)}
    SET_SERVO SERVO=dryer_vent ANGLE=180
    SET_SERVO SERVO=dryer_vent WIDTH=0
    SET_FAN_SPEED FAN=vent_fan SPEED=0

[gcode_macro DRY_FILAMENT]
rename_existing: BASE_DRY_FILAMENT
gcode:
    {% set minutes = params.MINUTES | default(120) %}
    {% set temp = params.TEMP | default(70) %}
    BASE_DRY_FILAMENT MINUTES={minutes} TEMP={temp}

[gcode_macro STOP_FILAMENT_DRYER]
rename_existing: BASE_STOP_FILAMENT_DRYER
gcode:
    BASE_STOP_FILAMENT_DRYER
</pre>
