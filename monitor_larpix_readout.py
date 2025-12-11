import threading
import time
import json
#from run_longevity_test.py import run
#from influxdb_config import token, ORG, url, BUCKET
#import influxdb_client, os, time
#from influxdb_client import InfluxDBClient, Point, WritePrecision
#from influxdb_client.client.write_api import SYNCHRONOUS
#import calculate_power_on_command

def measure_idda_vdda_iddd_vddd(healthy_list, baseline_file, result_container, readback_failure):

    # Retrieve vdda, idda, vddd and iddd for baseline
    with open(baseline_file, 'r') as json_file:
        dict_B = json.load(json_file)
    vdda_B, idda_B, vddd_B, iddd_B = [], [], [], []
    for tile in [1,2,3,4]:
        vdda_B.append(dict_B[f'tile{tile}']['vdda'])
        idda_B.append(dict_B[f'tile{tile}']['idda'])
        vddd_B.append(dict_B[f'tile{tile}']['vddd'])
        iddd_B.append(dict_B[f'tile{tile}']['iddd'])

    # Load controller
    c = larpix.Controller()
    c.io = larpix.io.PACMAN_IO(relaxed=True, asic_version=3)
    io_group = 1
    pacman_version = 'v1rev4'

    # Connect to InfluxDB
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Count number of failures, start with 0 per tile
    n_failure = [0,0,0,0,0,0,0,0]

    # Create dictionary for output reading
    dict_readback = {}

    # 60 iterations of 10 seconds each
    for iteration in range(0,4):

        # Create sub-dictionary for iteration number
        dict_readback[f'readback{iteration}'] = {}

        # List of dead tiles per iteration
        dead_tiles = []

        # Only check healthy tiles
        for tile in healthy_list:

            # Create sub-dictionary for healthy tile
            dict_readback[f'readback{iteration}'][f'tile{tile}'] = {}

            # Collect iddd, idda, vddd and vdda
            readback = power_readback(c.io, io_group, pacman_version, [tile])
            vdda = readback[tile][0]
            idda = readback[tile][1]
            vddd = readback[tile][2]
            iddd = readback[tile][3]

            # Save information to dictionary
            dict_readback[f'readback{iteration}'][f'tile{tile}']['timestamp'] = time.time()
            dict_readback[f'readback{iteration}'][f'tile{tile}']['idda'] = idda
            dict_readback[f'readback{iteration}'][f'tile{tile}']['iddd'] = iddd
            dict_readback[f'readback{iteration}'][f'tile{tile}']['vdda'] = vdda
            dict_readback[f'readback{iteration}'][f'tile{tile}']['vddd'] = vddd

            # Save information to InfluxDB
            point_vdda = (Point("pacman_boards").field("vdda", vdda).tag("tile", tile))
            point_idda = (Point("pacman_boards").field("idda", idda).tag("tile", tile))
            point_vddd = (Point("pacman_boards").field("vddd", vddd).tag("tile", tile))
            point_iddd = (Point("pacman_boards").field("iddd", iddd).tag("tile", tile))
            for point in [point_vdda, point_idda, point_vddd, point_iddd]:
                write_api.write(bucket=BUCKET, org=ORG, record=point)

            # Perform failure test
            failure_bool, idda_perc, iddd_perc = readout_failure(vdda_B[tile-1], idda_B[tile-1], vddd_B[tile-1], iddd_B[tile-1], vdda, idda, vddd, iddd)
            point_idda_perc = (Point("pacman_boards").field("failure_idda", idda_perc).tag("tile", tile))
            point_iddd_perc = (Point("pacman_boards").field("failure_iddd", iddd_perc).tag("tile", tile))
            for point in [point_idda_perc, point_iddd_perc]:
                write_api.write(bucket=BUCKET, org=ORG, record=point)

            # If failure
            if tile==1 or tile==7: # if failure_bool==True:

                # Update list of failures
                n_failure[tile-1] = n_failure[tile-1] + 1
                dict_readback[f'readback{iteration}'][f'tile{tile}']['n_failure'] = n_failure[tile-1]

                # If 3 consecutive failures
                if n_failure[tile-1]==3:

                    # Update failure flag
                    readback_failure[0] = True

                    # Update list of dead tiles
                    dead_tiles.append(tile)

            else: 
                
                # Update number of failures back to 0
                n_failure[tile-1] = 0
                dict_readback[f'readback{iteration}'][f'tile{tile}']['n_failure'] = n_failure[tile-1]
            

        # Update list of healthy tiles at the end of each iteration
        healthy_list = [x for x in healthy_list if x not in dead_tiles]

        # If there was a failure, restart the boards and only power on the healthy ones
        if readback_failure[0]==True:

            # Power off all boards
            print('python3 power_off.py')

            # Power on healthy boards
            #command_tiles, command_vdda, command_vddd = calculate_power_on_command.main(healthy_tiles)
            print(f'python3 power_on.py --pacman_tile {healthy_tiles} --vdda {command_vdda} --vddd {command_vddd}')
            print(f'python3 network_single_chip_pedestal.py --pacman_tile {healthy_tiles}')
                
        time.sleep(1) # 60 iterations of 10s = 10 minutes

    # Update result_container with most up-to-date list of healthy tiles
    for n in range(0,len(healthy_list)):
        result_container.append(healthy_list[n])

    #print(json.dumps(dict_readback, indent=4))


def measure_v_pedestal():

    for n in range(0,3):
        #print(f'Pedestal, iteraction #{n}')
        time.sleep(1)

def main(healthy_boards, baseline_file):

    # shared containers
    output_healthy_boards = [] # list of healthy tiles after monitoring readback variables for 10 minutes
    readback_failure = [False] # flag to indicate failure at readback variables, start with False
    
    # create threads
    t1 = threading.Thread(target=measure_idda_vdda_iddd_vddd, args=(healthy_boards, baseline_file, output_healthy_boards, readback_failure))
    t2 = threading.Thread(target=measure_v_pedestal, args=())

    # start both at the same time
    t1.start()
    t2.start()

    # wait until both are done
    t1.join()
    t2.join()

    # After both processes are done, only perform failure check for v_pedestal if there was no failure for readback variables
    if readback_failure[0]==True:
        print('There was a readback failure! Skip failure check for v_pedestal.')
    else:
        # Perform failure check for v_pedestal
        print('No readback failure. Perform failure test for v_pedestal!')

    return output_healthy_boards

if __name__ == "__main__":

    print('Input healthy tiles: [1]')
    healthy_tiles = main([1], 'baseline_2025_12_11_12_53_28.json')
    print(f'Output healthy tiles: {healthy_tiles}')