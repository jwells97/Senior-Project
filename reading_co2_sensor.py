# Reads in data from CO2 sensor in bytes
# To check available ports, run the following in Anaconda:
# python -m serial.tools.list_ports

import serial
import time
import array
from pymongo import MongoClient
import time
import threading
from PyQt5.QtCore import QTimer

# Establishes the connection to the MongoDB database client.
# Now reads in a recognizable PPM value.
# program reads in data from the co2 sensor from communications port 3 and stores in the dataList list as a float.
# Tries to run the code, if it fails it should toss an error about the port not being found.
# Should also close the port as code is stopped.
comPort = 'COM7'

def read_input():
        client = MongoClient('mongodb://localhost:27017')
        db = client.CO2_Sensor_Data
        try:
            ser = serial.Serial(comPort)
            ser.flushInput()
            time.sleep(1)
            ser.write(bytearray([0xFE, 0x44, 0x00, 0x08, 0x02, 0x9F, 0x25]))
            time.sleep(.01)
            response = ser.read(7)
            high = response[3]
            low = response[4]
            co2_levels = (high*256) + low
            collection1 = db.raw_data
            co2_data = {
                'CO2 Level': co2_levels,
                'Time': time.asctime(time.localtime()),
                'ComputerTime': time.mktime(time.localtime())
            }
            collection1.insert_one(co2_data)
            

        

        except ValueError:
            print("If port was not found, try using the command: python -m serial.tools.list_ports in the anaconda terminal.")
        finally:
            ser.close()
# update function that updates data/database
#try making qtimer here that calls function inside file to fix threading issue.
def init_input_timer():
        while True:
            read_input()
            time.sleep(6)
        #timers = []
        #timer1 = threading.Timer(1.0,read_input)
        #timer1.start()
        #timers.append(timer1)

thread = threading.Thread(target=init_input_timer,daemon=True)
thread.start() 
