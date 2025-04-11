from sensor_monitor.sensor import Sensor
from sensor_monitor.config import SENSOR_FILE
from sensor_monitor.mqtt import MQTTPublisher
from sensor_monitor.logger import sensor_logger


import json
import board

class SensorManager:
    def __init__(self):
        self.logger = sensor_logger()
        self.i2c = board.I2C()
        self.sensors = self.load_sensors()
        self.mqtt = MQTTPublisher()
        self.load_mqtt_discovery()  


    def detect_sensors(self):
        
        while not self.i2c.try_lock():
                pass
        try:
            while True:
                addresses = self.i2c.scan()
                self.logger.info("I2C addresses found:")
                for address in addresses:
                    self.logger.info(str(address))
                print(
                    "I2C addresses found:",
                    [hex(device_address) for device_address in self.i2c.scan()],
                )
                return addresses
        finally:
            self.i2c.unlock()     
    
    def load_sensors(self):

        sensors = []

        try:
            with open(SENSOR_FILE, "r") as f:
                sensor_data = json.load(f)
                sensors = [Sensor(s["name"], s["address"], s["type"]) for s in sensor_data]
                self.logger.info("Configured Sensor:")

                for sensor in self.sensors:
                    self.logger.info(str(sensor))
                
            
        except:
            pass

        existing_sensors = [s.address for s in sensors]
        connected_sensors = self.detect_sensors()

        for addr in connected_sensors:
            if addr not in existing_sensors:
                default_name = f"Sensor_{addr}"
                default_type = "solar"
                sensors.append(Sensor(default_name, addr, default_type))

        self.save_sensors(sensors)
        return sensors

    def load_mqtt_discovery(self):
        try:
            for sensor in self.sensors:
                self.mqtt.send_discovery_config(sensor.name)
                
        except:
            pass

    def publish_mqtt (self, data):
        try:
            self.mqtt.publish(data)
                
        except:
            pass
        
        
    def new_sensor(self):
        sensor = [Sensor("New", 64, "solar")]
        self.save_sensors(sensor)
        self.sensors = self.load_sensors()


    def save_sensors(self, sensors=None):
        if sensors is None:
            sensors = self.sensors
        with open(SENSOR_FILE, "w") as f:
            json.dump([{"name": s.name, "address": s.address, "type": s.type} for s in sensors], f)

    def update_sensor(self, name, new_name, new_type):
        for sensor in self.sensors:
            if sensor.name == name:
                sensor.name = new_name
                sensor.type = new_type
                self.save_sensors()
                self.mqtt.send_discovery_config(sensor.name)
                return True
        return False

    def get_data(self):
        return {s.name: s.read_data() for s in self.sensors}
    