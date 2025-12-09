# Author: Marina Reggiani-Guzzo
# Last modified: 8-Dec-2025
#
# Description: 
# This script performs the failure tests on the information collected
# from the LArPix boards. It is calculating the percentual value of IDDD, IDDA, VDDD
# and VDDA in comparison to the baseline collected at the beginning of the longevity
# test. This percentual value is saved into InfluxDB, that populates our Grafana page.

# Output:
# - Print statement with array of healthy boards.
# - InfluxDB is populated with variables used on failure test: percentual difference for 
# iddd and idda between latest measurement and original baseline, as well as the number
# of channels per tile with mean v_pedestal outside acceptable range.

# How to run:
# python3 failure_test.py --baseline /path/to/baseline/dictionary --out_folder /path/to/last/saved/dictionary --pacman_tile 1 2 3 4 5 6 7 8

# Flag options:
# --baseline: path to baseline dictionary
# --out_folder: path to folder with latest dictionary saved
# --pacman_tile: list of pacman tiles (from 1-8)

import argparse
import json
import glob

from influxdb_config import token, ORG, url, BUCKET

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', '-b', type=str, help='Path to dictionary with baseline information')
    parser.add_argument('--out_folder', type=str, help='Path to folder with .h5 and dictionary files')
    parser.add_argument('--pacman_tile', nargs='+', type=int, help='List of pacman tiles, from 1-8')
    args = parser.parse_args()

    # open dictionary with original baseline information
    with open(args.baseline, 'r') as json_file0:
        dict0 = json.load(json_file0)

    # open latest dictionary saved in out_folder
    list_of_files = glob.glob(f'{args.out_folder}/*.json')
    latest_file = max(list_of_files, key=os.path.getctime)
    with open(latest_file, 'r') as json_file1:
        dict1 = json.load(json_file1)

    # Connection to InfluxDB
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # array with healthy boards
    healthy_boards = []

    for tile in args.pacman_tile:

        # retrieve idda
        idda0 = dict0[f'tile{tile}']['idda']
        idda1 = dict1[f'tile{tile}']['idda']

        # retrieve iddd
        iddd0 = dict0[f'tile{tile}']['iddd']
        iddd1 = dict1[f'tile{tile}']['iddd']
        
        # calculate mean pedestal
        v_mean_pedestal0 = 0
        for ch in range(0,64):
            v_mean_pedestal0 = v_mean_pedestal0 + (dict0[f'tile{tile}']['pedestal'][f'ch_{ch}']/64)

        # count number of channels falling outside 50% < v_mean_pedestal0 < 150% range
        # failure happens when count>6
        count_v_pedestal = 0
        for ch in range(0,64):
            v_pedestal_ch = dict1[f'tile{tile}']['pedestal'][f'ch_{ch}']
            if (v_pedestal_ch < (0.5*v_mean_pedestal0)) or (v_pedestal_ch > (1.5*v_mean_pedestal0)):
                count_v_pedestal = count_v_pedestal + 1
        
        # calculate percentage for iddd and idda
        idda_perc = (idda1/idda0) * 100
        iddd_perc = (iddd1/iddd0) * 100

        # save information to InfluxDB
        point_pedestal = (Point("pacman_boards").field("failure_pedestal", count_v_pedestal).tag("tile", tile))
        write_api.write(bucket=BUCKET, org=ORG, record=point_pedestal)

        point_idda = (Point("pacman_boards").field("failure_idda", idda_perc).tag("tile", tile))
        write_api.write(bucket=BUCKET, org=ORG, record=point_idda)

        point_iddd = (Point("pacman_boards").field("failure_iddd", iddd_perc).tag("tile", tile))
        write_api.write(bucket=BUCKET, org=ORG, record=point_iddd)

        # perform failure test
        if idda_perc>150 or iddd_perc>150 or count_v_pedestal>6:
            healthy_boards.append(tile)
        
    # Close InfluxDB client
    client.close()

    print(healthy_boards)
        