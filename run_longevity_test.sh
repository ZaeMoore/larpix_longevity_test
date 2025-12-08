#!/bin/bash

# This script is inteded to run the longevity test for LArPix chips over the course of 3 months
# It will run step 1 once a day at the same time, and run step 2 for the rest of the day
# It will save data in subdirectories created every week

# Set initial day and time t0
current_day=$(date +%Y-%m-%d)
current_time=$(date +%H:%M)
t0=$(date +%H:%M)
d0=$(date +%Y-%m-%d)

# Set the seconds counter to 0 (this will count time since last step 1 execution finished)
SECONDS=0

# Convert t0 to minutes
t0_h=${t0:0:2}
t0_m=${t0:3:2}
t0_minutes=$((10#$t0_h * 60 + 10#$t0_m))

echo -e "Starting longevity test script.\nStart day d0 = $current_day. Start time t0 = $current_time.\n"

# Initial time in seconds for week 0
w0_s=$(date +%s)
directory="su_cryolongevity_$(date +%Y-%m-%d)"
mkdir $directory

# Begin recording data
while true; do 

    current_day=$(date +%Y-%m-%d)
    current_time=$(date +%H:%M)
    echo -e "\n\nCurrent day: $current_day. Current time: $current_time."

    current_time_h=${current_time:0:2}
    current_time_m=${current_time:3:2}
    current_time_minutes=$((10#$current_time_h * 60 + 10#$current_time_m))

    echo "Step 1 runs at time t0 = $t0"

    time_difference=$((10#$current_time_minutes - 10#$t0_minutes))
    echo "Current time - t0 difference in minutes: $time_difference"

    echo -e "Seconds since step 1 last finished: $SECONDS\n"

    # If current time t-t0<10min, run step 1
    # Main check
    if [[ $time_difference -lt 10  && $time_difference -gt -1 ]]; then

        # If a week has passed since a subdirectory was last created for storing data, create a new one
        week_difference=$((10#$(date +%s) - 10#$w0_s))
        if [[ 10#$week_difference -gt 604800 ]]; then
            w0_s=$(date +%s) #Update week 0 time
            echo "Creating new subdirectory for the week"
            directory="su_cryolongevity_$(date +%Y-%m-%d)"
            mkdir $directory

        fi

        echo "Collect baseline with nominal voltages"

        # Set 8 samples to nominal voltage
        echo "Power on script with nominal voltages"
        python3 power_on.py --pacman_tile 1,2,3,4,5,6,7,8 --vdda 5243 --vddd 26214

        # Set boards to pedestal mode
        echo "Pedestal mode script"
        python3 network_single_chip_pedestal.py --pacman_tile 1,2,3,4,5,6,7,8

        # Run baseline collection script
        # It collects vdda, idda, vddd, iddd and pedestal for all channels (daq=10min) and runs failure tests
        # Flag options:
        # --daq: Duration of data acquisition, in seconds
        # --outloc: Where do you want to save information? 1=influxdb, 2=dictionary, 3=both
        # -p, --pathoutfile: Path to where to save the .h5 files and dictionaries
        # --pacman_tile: List of pacman tiles, from 1-8
        # --baseline: Path to dictionary file with initial parameters
        echo "Baseline collection script"
        python3 measure_baseline.py --daq 600 --outloc 3 -p $directory --pacman_tile 1 2 3 4 5 6 7 8 --baseline /path/to/initial/baseline/parameters

        SECONDS=0

    # If it has been more than 24 hours since step 1 last ended, run step 1 again
    # Backup check
    elif [[ 10#$SECONDS -gt 86400 ]]; then

        echo "Collect baseline with nominal voltages"

        # Set 8 samples to nominal voltage
        echo "Power on script with nominal voltages"
        python3 power_on.py --pacman_tile 1,2,3,4,5,6,7,8 --vdda 5243 --vddd 26214

        # Set boards to pedestal mode
        echo "Pedestal mode script"
        python3 network_single_chip_pedestal.py --pacman_tile 1,2,3,4,5,6,7,8

        # Run baseline collection script
        # It collects vdda, idda, vddd, iddd and pedestal for all channels (daq=10min) and runs failure tests
        # Flag options:
        # --daq: Duration of data acquisition, in seconds
        # --outloc: Where do you want to save information? 1=influxdb, 2=dictionary, 3=both
        # -p, --pathoutfile: Path to where to save the .h5 files and dictionaries
        # --pacman_tile: List of pacman tiles, from 1-8
        # --baseline: Path to dictionary file with initial parameters
        echo "Baseline collection script"
        python3 measure_baseline.py --daq 600 --outloc 3 -p $directory --pacman_tile 1 2 3 4 5 6 7 8 --baseline /path/to/initial/baseline/parameters

        SECONDS=0
    
    else

        echo "Collect baseline with accelerated voltages"

        # If current time t-t0>10min, run step 2
        # Set accelerated voltages, tile=1 is used as baseline with nominal voltage
        echo "Power on script with accelerated voltages"
        python3 power_on.py --pacman_tile 1,2,3,4,5,6,7,8 --vdda 5243,15729,15729,23593,23593,34079,34079,34079 --vddd 26214,30933,30933,35389,35389,40108,40108,40108

        # Set boards to pedestal mode
        echo "Pedestal mode script"
        python3 network_single_chip_pedestal.py --pacman_tile 1,2,3,4,5,6,7,8

        # Run baseline collection script
        # It collects vdda, idda, vddd, iddd and pedestal for all channels (daq=10min) and runs failure tests
        # Flag options:
        # --daq: Duration of data acquisition, in seconds
        # --outloc: Where do you want to save information? 1=influxdb, 2=dictionary, 3=both
        # -p, --pathoutfile: Path to where to save the .h5 files and dictionaries
        # --pacman_tile: List of pacman tiles, from 1-8
        # --baseline: Path to dictionary file with initial parameters
        echo "Baseline collection script"
        python3 measure_baseline.py --daq 600 --outloc 3 -p $directory --pacman_tile 1 2 3 4 5 6 7 8 --baseline /path/to/initial/baseline/parameters

    fi 

done
