# Authors: Marina Reggiani-Guzzo, Zae Moore (Syracuse University)
# Last modified: 12-Dec-2025
#
# Description: 
# This script performs the failure tests on the information collected
# from the LArPix boards. It is calculating the percentual value of IDDD, IDDA, VDDD
# and VDDA in comparison to the baseline collected at the beginning of the longevity
# test. This percentual value is saved into InfluxDB, that populates our Grafana page.


import json
import glob

from influxdb_config import token, ORG, url, BUCKET

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


# Failure test for pedestal  
# Pass every tile in healthy_tiles array
# Input: baseline_path [string], latest_path [string], healthy_tiles [array]
# Output: True for healthy/False for failure, pedestal_count [array]
def pedestal_failure(baseline_path, latest_path, healthy_tiles):
    failure = [True, True, True, True, True, True, True, True]
    pedestal_count = [0, 0, 0, 0, 0, 0, 0, 0]

    # open dictionary with original baseline information
    with open(baseline_path, 'r') as json_file0:
        dict0 = json.load(json_file0)

    # open dictionary with original baseline information
    with open(latest_path, 'r') as json_file0:
        dict1 = json.load(json_file0)

    for index, tile in enumerate(healthy_tiles):

        # calculate mean pedestal for initial baseline
        v_mean_pedestal0 = 0
        for ch in range(0,64):
            v_mean_pedestal0 = v_mean_pedestal0 + (dict0[f'tile{tile}'][f'channel{ch}']['v_pedestal']/64)

        # count number of channels falling outside 50% < v_mean_pedestal0 < 150% range
        # failure happens when count>6
        count_v_pedestal = 0
        for ch in range(0,64):
            v_pedestal_ch = dict1[f'tile{tile}'][f'channel{ch}']['v_pedestal']
            if (v_pedestal_ch < (0.5*v_mean_pedestal0)) or (v_pedestal_ch > (1.5*v_mean_pedestal0)):
                count_v_pedestal = count_v_pedestal + 1

        pedestal_count[index] = count_v_pedestal

        if count_v_pedestal>6:
            failure[index] = False

    return failure, pedestal_count


# Failure test for readout idda and iddd
# Pass values for one individual tile at a time
# Input: baseline idda, baseline iddd, current idda, current iddd
# Output: True for healthy/False for failure, idda percentage, iddd percentage
def readout_failure(idda_baseline, iddd_baseline, idda, iddd):

    # Calculate percentage for iddd and idda
    idda_perc = float((idda/idda_baseline) * 100)
    iddd_perc = float((iddd/iddd_baseline) * 100)

    # Failure test for readout
    if idda_perc>150 or iddd_perc>150:
        return False, idda_perc, iddd_perc
    else:
        return True, idda_perc, iddd_perc
