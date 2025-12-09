# Author: Marina Reggiani-Guzzo
# Last modified: 9-Dec-2025

# Description:
# Collects the following information from the CTC100 and populates InfluxDB with it.
# - Temperature at the heater
# - Pressure at the cold head
# - Voltage applied to the pressure gauge sensor
# - Power applied to the heater 

from influxdb_config import token, ORG, url, BUCKET
import argparse
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import serial

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--sleeptime', default=10, type=int, help='Time interval in between daq')
    args = parser.parse_args()

    client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # this dictionary links the variable to its position in the "response" variable (line 30)
    dict = {
        "temperature": 0,
        "voltage": 16,
        "pressure": 17,
        "heater": 6
    }

    ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

    while True:

        ser.write(b'getOutput?\n')
        response = ser.readline().decode().strip()

        temperature = float(response.split(',')[dict.get("temperature")])
        voltage = float(response.split(',')[dict.get("voltage")])
        pressure = float(response.split(',')[dict.get("pressure")])
        heater = float(response.split(',')[dict.get("heater")])

        point_temp = (Point("ctc").field("temperature", temperature))
        point_voltage = (Point("ctc").field("voltage", voltage))
        point_pressure = (Point("ctc").field("pressure", pressure))
        point_heater = (Point("ctc").field("heater", heater))

        write_api.write(bucket=BUCKET, org=ORG, record=point_temp)
        write_api.write(bucket=BUCKET, org=ORG, record=point_voltage)
        write_api.write(bucket=BUCKET, org=ORG, record=point_pressure)
        write_api.write(bucket=BUCKET, org=ORG, record=point_heater)

        time.sleep(args.sleeptime)
