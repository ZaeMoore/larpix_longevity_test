# Author: Marina Reggiani-Guzzo (Syracuse University)
# Last modified: 15 October 2025
#
# Description: This script collects the vddd, iddd, vdda, idda for all pacman tiles,
# as well as the mean pedestal and the number of packets of each channel. The information
# is saved into a dictionary under ../output_data/baseline_YYYY_MM_DD.json
#
# How to run:
# > python3 measure_baseline.py --daq 60 --outloc 3 --pacman_tile 1 2 3 4 5 6 7 8 --out_folder /path/to/folder
# 
# Flag options:
# --daq: Duration of data acquisition, in seconds
# --outloc: Where do you want to save information? 1=influxdb, 2=dictionary, 3=both
# --pacman_tile: List of pacman tiles, from 1-8
# --out_folder: Path to folder to save .h5 files and dictionaries

import larpix
import larpix.io 

from util import data, save_controller
from power_on import power_readback

import argparse
import glob
import h5py
import json
import numpy as np
from datetime import datetime
from influxdb_config import token, ORG, url, BUCKET

import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import influxdb_config

def create_dictionary(tile_list):

    dict = {}
    for tile in tile_list:
        dict[f'tile{str(tile)}'] = {}
        dict[f'tile{str(tile)}']['pedestal'] = {}
        dict[f'tile{str(tile)}']['packets'] = {}
    
    return dict

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--daq', default=600, type=int, help='Duration of data acquisition, in seconds')
    parser.add_argument('--outloc', type=int, help='Where do you want to save information? 1=influxdb, 2=dictionary, 3=both')
    parser.add_argument('-l', '--pacman_tile', nargs='+', type=int, required=True, help='List of pacman tiles, from 1-8')
    parser.add_argument('--out_folder', type=str, help='Path to folder to save dictionary and .h5 files')
    args = parser.parse_args()

    # Connection to InfluxDB
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Load controller
    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True, asic_version=3)

    # Collect data and save output under args.out_folder/packet-YYYY_MM_DD_HH_MM_SS_EDT.h5
    data(c, args.daq, data_dir=args.out_folder, tag=None)

    # Retrieve name of the file just created
    list_of_files = glob.glob(f'{args.out_folder}/*.h5')
    latest_file = max(list_of_files, key=os.path.getctime)

    # Open correct information within file
    f = h5py.File(latest_file)
    p = f['packets']
    d = p[p['packet_type'] == 1]
    
    if args.outloc == 2 or args.outloc == 3:
        dict = create_dictionary(args.pacman_tile)
    
    for tile in args.pacman_tile:

        # Retrieve vddd, iddd, vdda, idda
        io_group = 1
        pacman_version = 'v1rev4'
        readback = power_readback(c.io, io_group, pacman_version, [tile])

        if args.outloc == 2 or args.outloc == 3:
            dict[f'tile{tile}']['vdda'] = readback[tile][0]
            dict[f'tile{tile}']['idda'] = readback[tile][1]
            dict[f'tile{tile}']['vddd'] = readback[tile][2]
            dict[f'tile{tile}']['iddd'] = readback[tile][3]

        if args.outloc == 1 or args.outloc == 3:
            point_vdda = (Point("pacman_boards").field("vdda", readback[tile][0]).tag("tile", tile))
            point_idda = (Point("pacman_boards").field("idda", readback[tile][1]).tag("tile", tile))
            point_vddd = (Point("pacman_boards").field("vddd", readback[tile][2]).tag("tile", tile))
            point_iddd = (Point("pacman_boards").field("iddd", readback[tile][3]).tag("tile", tile))
            for point in [point_vdda, point_idda, point_vddd, point_iddd]:
                write_api.write(bucket=BUCKET, org=ORG, record=point)

        io_channel = ( int(tile) - 1) * 4 + 1
        d_io = d[d['io_channel'] == io_channel]
        
        for channel_id in range(64):
            d_channel = d_io[d_io['channel_id'] == channel_id]

            mean_pedestal = np.mean(d_channel['dataword'])
            packets = len(d_channel)

            if args.outloc == 2 or args.outloc == 3:
                dict[f'tile{tile}']['pedestal'][f'ch_{channel_id}'] = mean_pedestal
                dict[f'tile{tile}']['packets'][f'ch_{channel_id}'] = packets

            if args.outloc == 1 or args.outloc == 3:
                point = (Point("pacman_boards").field("mean_pedestal", mean_pedestal).tag("tile", tile).tag("channel_id", channel_id))
                write_api.write(bucket=BUCKET, org=ORG, record=point)
                point = (Point("pacman_boards").field("packets", packets).tag("tile", tile).tag("channel_id", channel_id))
                write_api.write(bucket=BUCKET, org=ORG, record=point)

    if args.outloc == 2 or args.outloc == 3:
        # Save dictionary to a file
        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        with open(f'{args.out_folder}/baseline_{timestamp}.json', 'w') as f:
            json.dump(dict, f, indent=4)

    # Close InfluxDB client
    client.close()