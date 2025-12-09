# Author: Marina Reggiani-Guzzo
# Last modified: 9-Dec-2025

# Description:
# Collects the following information from the compressor and populates InfluxDB with it.
# - Compressor status: string and numerical value (1=Running, 2=Idle)
# - Water temperature in and out
# - Low and high pressure
# - Low and high average pressure
# - Warning and alarm numbers

import argparse

# InfluxDB
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_config import token, ORG, url, BUCKET

# Compressor
import socket
import struct
from tkinter import Tk, Button, INSERT, END, Label, Text
from tkinter import scrolledtext

def buildRegistersQuery():
    query = bytes([0x09, 0x99,  # Message ID
                   0x00, 0x00,  # Unused
                   0x00, 0x06,  # Message size in bytes
                   0x01,        # Slave Address
                   0x04,        # Function Code  3= Read HOLDING registers, 4 read INPUT registers
                   0x00,0x01,   # The starting Register Number
                   0x00,0x37])  # How many to read
    return query

def FloatToString(theNumber):
    fNumber = round(theNumber, 1)
    return str(fNumber)

def buildMessage(code):
    strReturn = "  "
    worker = code
    if (1073741824 <= worker):
        strReturn += "Inverter Comm Loss, "
        worker -= 1073741824
    if (536870912 <= worker):
        strReturn += "Driver Comm Loss, "
        worker -= 536870912
    if (268435456 <= worker):
        strReturn += "Inverter Error, "
        worker -= 268435456
    if (134217728 <= worker):
        strReturn += "Motor Current High, "
        worker -= 134217728
    if (67108864 <= worker):
        strReturn += "Motor Current Sensor, "
        worker -= 67108864
    if (33554432 <= worker):
        strReturn += "Low Pressure Sensor, "
        worker -= 33554432
    if (16777216 <= worker):
        strReturn += "High Pressure Sensor, "
        worker -= 16777216
    if (8388608 <= worker):
        strReturn += "Oil Sensor, "
        worker -= 8388608
    if (4194304 <= worker):
        strReturn += "Helium Sensor, "
        worker -= 4194304
    if (2097152 <= worker):
        strReturn += "Coolant Out Sensor, "
        worker -= 2097152
    if (1048576 <= worker):
        strReturn += "Coolant In Sensor, "
        worker -= 1048576
    if (524288 <= worker):
        strReturn += "Motor Stall, "
        worker -= 524288
    if (262144 <= worker):
        strReturn += "Static Pressure Low, "
        worker -= 262144
    if (131072 <= worker):
        strReturn += "Static Pressure High, "
        worker -= 131072
    if (65536 <= worker):
        strReturn += "Power Supply Error, "
        worker -= 65536
    if (32768 <= worker):
        strReturn += "Three Phase Error, "
        worker -= 32768 
    if (16384 <= worker):
        strReturn += "Motor Current Low, "
        worker -= 16384
    if (8192 <= worker):
        strReturn += "Delta Pressure Low, "
        worker -= 8192
    if (4096 <= worker):
        strReturn += "Delta Pressure High, "
        worker -= 4096
    if (2048 <= worker):
        strReturn += "High Pressure Low, "
        worker -= 2048
    if (1024 <= worker):
        strReturn += "High Pressure High, "
        worker -= 1024
    if (512 <= worker):
        strReturn += "Low Pressure Low, "
        worker -= 512
    if (256 <= worker):
        strReturn += "Low Pressure High, "
        worker -= 256
    if (128 <= worker):
        strReturn += "Helium Low, "
        worker -= 128
    if (64 <= worker):
        strReturn += "Helium High, "
        worker -= 64
    if (32 <= worker):
        strReturn += "Oil Low, "
        worker -= 32
    if (16 <= worker):
        strReturn += "Oil High, "
        worker -= 16
    if (8 <= worker):
        strReturn += "Coolant Out Low, "
        worker -= 8
    if (4 <= worker):
        strReturn += "Coolant Out High, "
        worker -= 4
    if (2 <= worker):
        strReturn += "Coolant In Low, "
        worker -= 2
    if (1 <= worker):
        strReturn += "Coolant In High, "
        worker -= 1
    #remove the final space & Comma if we have a message
    if (0 < len(strReturn.strip())):
        strReturn = strReturn.strip()
        strReturn = strReturn[0:len(strReturn)-1]
    else:
        strReturn = 'None'
    return strReturn

def buildCompressorState(stateNumber):
    return 'Running' if 0 < stateNumber else 'Idle' 

def buildOperatingState(stateNumber):
    strReturn = 'Unknown State'
    if 0 == stateNumber:
        strReturn = 'Ready to start'
    elif 2 == stateNumber:
        strReturn = 'Starting'
    elif 3 == stateNumber:
        strReturn = 'Running'
    elif 5 == stateNumber:
        strReturn = 'Stopping'
    elif 6 == stateNumber:
        strReturn = 'Error Lockout'
    elif 7 == stateNumber:
        strReturn = 'Error'
    elif 8 == stateNumber:
        strReturn = 'Helium Overtemp Cooldown'
    elif 9 == stateNumber:
        strReturn = 'Power Related Error'
    elif 15 == stateNumber:
        strReturn = 'Recovered From Error'
    return strReturn 

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--sleeptime', default=10, type=int, help='Time interval in between daq')
    args = parser.parse_args()

    HOST = '10.42.0.119'
    HOST = HOST.strip()
    PORT = 502

    # InfluxDB
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    while True:

        # create connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(buildRegistersQuery())
            rawData = s.recv(1024)
            s.close()

        # information saved into influxDB
        wkrBytes = bytes([rawData[11], rawData[12]])
        iPumpState = int.from_bytes(wkrBytes, byteorder='big')
        point = (Point("compressors").field("compressor_state", buildCompressorState(iPumpState)).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        if buildCompressorState(iPumpState)=="Running":
            point = (Point("compressors").field("compressor_state_numerical", 1).tag("id", "global"))
            write_api.write(bucket=BUCKET, org=ORG, record=point)
        else:
            point = (Point("compressors").field("compressor_state_numerical", 0).tag("id", "global"))
            write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[87], rawData[88]])
        iCoolantIn = int.from_bytes(wkrBytes, byteorder='big')
        fCoolantIn = float(iCoolantIn) / 10.0
        fCoolantIn = round(fCoolantIn, 1)
        point = (Point("compressors").field("coolant_in", fCoolantIn).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[89], rawData[90]])
        iCoolantOut = int.from_bytes(wkrBytes, byteorder='big')
        fCoolantOut = float(iCoolantOut) / 10.0
        fCoolantOut = round(fCoolantOut, 1)
        point = (Point("compressors").field("coolant_out", fCoolantOut).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[95], rawData[96]])
        iLowPressure = int.from_bytes(wkrBytes, byteorder='big')
        fLowPressure = float(iLowPressure) / 10.0
        fLowPressure = round(fLowPressure, 1)
        point = (Point("compressors").field("low_pressure", fLowPressure).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[97], rawData[98]])
        iLowPressureAvg = int.from_bytes(wkrBytes, byteorder='big')
        fLowPressureAvg = float(iLowPressureAvg) / 10.0
        fLowPressureAvg = round(fLowPressureAvg, 1)
        point = (Point("compressors").field("low_pressure_avg", fLowPressureAvg).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[99], rawData[100]])
        iHighPressure = int.from_bytes(wkrBytes, byteorder='big')
        fHighPressure = float(iHighPressure) / 10.0
        fHighPressure = round(fHighPressure, 1)
        point = (Point("compressors").field("high_pressure", fHighPressure).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[101], rawData[102]])
        iHighPressureAvg = int.from_bytes(wkrBytes, byteorder='big')
        fHighPressureAvg = float(iHighPressureAvg) / 10.0
        fHighPressureAvg = round(fHighPressureAvg, 1)
        point = (Point("compressors").field("high_pressure_avg", fHighPressureAvg).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[113], rawData[114], rawData[111], rawData[112]])
        iWarn = int.from_bytes(wkrBytes, byteorder='big')
        point = (Point("compressors").field("warning_number", iWarn).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        wkrBytes = bytes([rawData[117], rawData[118], rawData[115], rawData[116]])
        iAlarm = int.from_bytes(wkrBytes, byteorder='big')
        point = (Point("compressors").field("alarm_number", iAlarm).tag("id", "global"))
        write_api.write(bucket=BUCKET, org=ORG, record=point)

        time.sleep(args.sleeptime)

    client.close()
