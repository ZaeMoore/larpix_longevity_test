# Author: Marina Reggiani-Guzzo
# Last modified: 9-Dec-2025

# Description:
# Collects the following information from the LabJack and populates InfluxDB with it.
# - Room temperature and humidity
# - Cryostat temperature from four probes installed in the cryostat
# - Cryostat pressure (voltage reading and converted to Torr)

from influxdb_config import token, ORG, url, BUCKET
import argparse
from labjack import ljm
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--sleeptime', default=10, type=int, help='Time interval in between daq')
    args = parser.parse_args()

    handle = ljm.openS("ANY","ANY","ANY")

    client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    while True:

        # Read information
        ch1_readout = ljm.eReadName(handle, "SBUS22_TEMP") # Room temperature
        ch2_readout = ljm.eReadName(handle, "SBUS22_RH") # Room Humidity
        ch3_readout = ljm.eReadName(handle, "AIN0_EF_READ_A") # Cryostat Temperature Top
        ch4_readout = ljm.eReadName(handle, "AIN4_EF_READ_A") # Cryostat Temperature Middle Top
        ch5_readout = ljm.eReadName(handle, "AIN6_EF_READ_A") # Cryostat Temperature Middle Bottom
        ch6_readout = ljm.eReadName(handle, "AIN8_EF_READ_A") # Cryostat Temperature Bottom
        ch7_readout = ljm.eReadName(handle, "AIN10") # Cryostat Pressure

        point1 = (Point("labjack").field("temperature", ch1_readout).tag("id", "room"))
        point2 = (Point("labjack").field("humidity", ch2_readout).tag("id", "room"))
        point3 = (Point("labjack").field("temperature", ch3_readout).tag("id", "cryostat").tag("location", "top"))
        point4 = (Point("labjack").field("temperature", ch4_readout).tag("id", "cryostat").tag("location", "topmiddle"))
        point5 = (Point("labjack").field("temperature", ch5_readout).tag("id", "cryostat").tag("location", "bottommiddle"))
        point6 = (Point("labjack").field("temperature", ch6_readout).tag("id", "cryostat").tag("location", "bottom"))
        point8 = (Point("labjack").field("pressure_voltage", ch7_readout).tag("id", "cryostat"))

        # convert voltage reading to pressure [Torr]
        ch7_readout = 10 ** (ch7_readout - 5)
        point7 = (Point("labjack").field("pressure", ch7_readout).tag("id", "cryostat"))
        

        for point in [point1, point2, point3, point4, point5, point6, point7, point8]:
            write_api.write(bucket=BUCKET, org=ORG, record=point)

        time.sleep(args.sleeptime)

    client.close()