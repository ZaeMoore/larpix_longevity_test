import threading
import time
import json
#from run_longevity_test.py import run
#from influxdb_config import token, ORG, url, BUCKET
#import influxdb_client, os, time
#from influxdb_client import InfluxDBClient, Point, WritePrecision
#from influxdb_client.client.write_api import SYNCHRONOUS
#import larpix
#import larpix.io 
#from util import data, save_controller
#from power_on import power_readback

#import calculate_power_on_command

def measure_idda_vdda_iddd_vddd(healthy_list, baseline_file, result_container, readback_failure, readout_file):

    # Retrieve vdda, idda, vddd and iddd for baseline
    with open(baseline_file, 'r') as json_file:
        dict_B = json.load(json_file)
    vdda_B, idda_B, vddd_B, iddd_B = [], [], [], []
    for tile in [1,2,3,4,5,6,7,8]:
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
    for iteration in range(0,5):

        print(f'Iteration {iteration}, healthy tiles: {healthy_list}')

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
            failure_bool, idda_perc, iddd_perc = False, float(200), float(200) # readout_failure(idda_B[tile-1], iddd_B[tile-1], idda, iddd)
            
            point_idda_perc = (Point("pacman_boards").field("failure_idda", idda_perc).tag("tile", tile))
            write_api.write(bucket=BUCKET, org=ORG, record=point_idda_perc)

            point_iddd_perc = (Point("pacman_boards").field("failure_iddd", iddd_perc).tag("tile", tile))
            write_api.write(bucket=BUCKET, org=ORG, record=point_iddd_perc)
                
            
            # If failure
            if tile==2: #if failure_bool==True:

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
            command_tiles, command_vdda, command_vddd = healthy_list, 5243, 26214 #calculate_power_on_command.main(healthy_list)
            print(f'python3 power_on.py --pacman_tile {healthy_list} --vdda {command_vdda} --vddd {command_vddd}')
            print(f'python3 network_single_chip_pedestal.py --pacman_tile {healthy_list}') 

            # Update failure bool
            readback_failure[0] = False
        
        time.sleep(1) # 60 iterations of 10s = 10 minutes 

    # Update result_container with most up-to-date list of healthy tiles
    for n in range(0,len(healthy_list)):
        result_container.append(healthy_list[n])

    # Save dictionary to file
    with open(readout_file, 'w') as f:
            json.dump(dict_readback, f, indent=4)

    print(json.dumps(dict_readback, indent=4))

def measure_v_pedestal(healthy_list, pedestal_file, weekly_folder):

    # DAQ time window, in seconds
    daq = 600

    # Create dictionary to save pedestal information
    dict_pedestal = {}
    dict_pedestal['timestamp'] = time.time()

    # Connection to InfluxDB
    #client = influxdb_client.InfluxDBClient(url=url, token=token, org=ORG)
    #write_api = client.write_api(write_options=SYNCHRONOUS)

    # Load controller
    #c = larpix.Controller()
    #c.io = larpix.io.PACMAN_IO(relaxed=True, asic_version=3)

    # Collect data and save output under args.out_folder/packet-YYYY_MM_DD_HH_MM_SS_EDT.h5
    #data(c, daq, data_dir=weekly_folder, tag=None)

    # Retrieve name of the file just created
    #list_of_files = glob.glob(f'{args.out_folder}/*.h5')
    #latest_file = max(list_of_files, key=os.path.getctime)

    # Open correct information within file
    #f = h5py.File(latest_file)
    #p = f['packets']
    #d = p[p['packet_type'] == 1]

    # Loop over healthy tiles and save information to a dictionary
    for tile in healthy_list:

        # Create sub-dictionary for healthy tiles
        dict_pedestal[f'tile{tile}'] = {}

        #io_channel = ( int(tile) - 1) * 4 + 1
        #d_io = d[d['io_channel'] == io_channel]

        for channel_id in range(64):

            # Create sub-sub-dictionary for channels
            dict_pedestal[f'tile{tile}'][f'channel{channel_id}'] = {}

            #d_channel = d_io[d_io['channel_id'] == channel_id]

            #mean_pedestal = np.mean(d_channel['dataword'])
            #packets = len(d_channel)

            dict_pedestal[f'tile{tile}'][f'channel{channel_id}']['v_pedestal'] = 1 #mean_pedestal
            dict_pedestal[f'tile{tile}'][f'channel{channel_id}']['packets'] = 2 #packets

    print(json.dumps(dict_pedestal, indent=4))

    # Save dictionary to file
    with open(pedestal_file, 'w') as f:
            json.dump(dict_pedestal, f, indent=4)



def main(healthy_boards, baseline_file, weekly_folder):

    # Input variables:
    # > healthy_boards: list of healthy boards by the time function is called, array format = [1,2,3,4]
    # > baseline_file: full path to dictionary containing baseline information, to be used for failure checks
    # > weekly_folder: full path to folder created weekly, it will be used to save pedestal_dict, readback_dict and .h5 files
    #
    # Description:
    # This function runs measure_idda_vdda_iddd_vddd() and measure_v_pedestal() in parallel. Once both processes
    # are complete, if there were no failure for readback variables during the 10-min window time, a failure check
    # is performed for the pedestal variables. The pedestal failure check is only performed if there was no readback
    # failure detected because, in case of readback failure, all boards are restarted during the 10-min window, which
    # impacts the pedestal data collection, and it was decided with Berkeley that in this case we should not perform
    # a pedestal failure check, just skip it.
    #
    # Return:
    # This function returns an updated list of healthy boards. 

    # shared containers
    output_healthy_boards = [] # list of healthy tiles after monitoring readback variables for 10 minutes
    readback_failure = [False] # flag to indicate failure at readback variables, start with False

    # Timestamp used for the file name with readback and pedestal dictionaries. They use the same timestamp to facilitate data matching later
    timestamp_for_file = datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    
    # create threads
    t1 = threading.Thread(target=measure_idda_vdda_iddd_vddd, args=(healthy_boards, 
                                                                    baseline_file, 
                                                                    output_healthy_boards, 
                                                                    readback_failure, 
                                                                    f'{weekly_folder}/{timestamp_for_file}_readback_dictionary.json'))

    t2 = threading.Thread(target=measure_v_pedestal, args=(healthy_boards, 
                                                           f'{weekly_folder}/{timestamp_for_file}_pedestal_dictionary.json', 
                                                           weekly_folder))

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

    #print('Input healthy tiles: [1,2,3,4]')
    #healthy_tiles = main([1,2,3,4], '../output_data/baseline_2025_12_09_10_27_51.json')
    #print(f'Output healthy tiles: {healthy_tiles}')

    measure_v_pedestal([1,2,3,4], 'output_data/pedestal_file.json', '/output_data')