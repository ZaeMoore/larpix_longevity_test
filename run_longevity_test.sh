#!/bin/bash

#Start running the script and start counting t0
#While t-t0<10min: run step 1
#If t-t0>10min: run step 2
#Perform failure test after step 1 and step 2. This will compare vddd, iddd, vdda, idda and pedestal of the designated
#baseline file (which should be the first one)
#Create a new subdirectory for each week to save data, once it becomes 7 days after initial day


# Set initial day and time t0
current_day=$(date +%Y-%m-%d)
current_time=$(date +%H:%M)
t0=$(date +%H:%M)
d0=$(date +%Y-%m-%d)
SECONDS=0
echo -e "Starting longevity test script.\nCurrent day: $current_day. Current time: $current_time"

t0_h=${t0:0:2}
t0_m=${t0:3:2}
t0_minutes=$((10#$t0_h * 60 + 10#$t0_m))
echo -e "t0 in minutes: $t0_minutes\n"

while true; do 

    current_day=$(date +%Y-%m-%d)
    current_time=$(date +%H:%M)
    echo "Current day: $current_day. Current time: $current_time"

    current_time_h=${current_time:0:2}
    current_time_m=${current_time:3:2}
    current_time_minutes=$((10#$current_time_h * 60 + 10#$current_time_m))
    echo "Current time in minutes: $current_time_minutes"

    time_difference=$((10#$current_time_minutes - 10#$t0_minutes))
    echo "Current time - t0 difference in minutes: $time_difference"

    echo -e "Seconds since step 1 last finished: $SECONDS\n"

    # If current time t-t0<10min, run step 1
    # Main check
    if [[ 10#$time_difference -lt 10 ]]; then

        echo "Collect baseline with nominal voltages"

        # Set 8 samples to nominal voltage
        #python3 power_on.py --vdda 51851 --pacman_tile 1,2,3,4,5,6,7,8
        echo "Power on script with nominal voltage"

        # Set boards to pedestal mode
        #python3 network_single_chip_pedestal.py --pacman_tile 1,2,3,4,5,6,7,8
        echo "Pedestal mode script"

        # Run baseline collection script. 
        # It collects vdda, idda, vddd, iddd and pedestal for all channels (daq=10min)
        # outloc options: 1=influxdb, 2=dictionary, 3=both
        #python3 measure_baseline.py --daq 600 --outloc 2
        echo "Baseline collection script (10 min)"

        # Check for failure
        #python3 failure_check.py
        echo -e "Failure check script\n"

        sleep 60

        SECONDS=0

    # If it has been more than 24 hours since step 1 last ended, run step 1 again
    # Backup check 86400
    elif [[ 10#$SECONDS -gt 86400 ]]; then

        echo "Collect baseline with nominal voltages"

        # Set 8 samples to nominal voltage
        #python3 power_on.py --vdda 51851 --pacman_tile 1,2,3,4,5,6,7,8
        echo "Power on script with nominal voltage"

        # Set boards to pedestal mode
        #python3 network_single_chip_pedestal.py --pacman_tile 1,2,3,4,5,6,7,8
        echo "Pedestal mode script"

        # Run baseline collection script. 
        # It collects vdda, idda, vddd, iddd and pedestal for all channels (daq=10min)
        # outloc options: 1=influxdb, 2=dictionary, 3=both
        #python3 measure_baseline.py --daq 600 --outloc 2
        echo "Baseline collection script (10 min)"

        # Check for failure
        #python3 failure_check.py
        echo -e "Failure check script\n"

        sleep 60

        SECONDS=0
    
    else

        echo "Collect baseline with accelerated voltages"

        # If current time t-t0>10min, run step 2
        # Set higher voltages, tile=1 is used as baseline with nominal voltage
        #python3 power_on.py --pacman_tile 2,3 --vdda <3.75V> --vddd <1.8V>
        #python3 power_on.py --pacman_tile 4,5 --vdda <4.38V> --vddd <2.10V>
        #python3 power_on.py --pacman_tile 6,7,8 --vdda <4.5V> --vddd <2.40V>
        echo "Power on script with accelerated voltages"

        # Set boards to pedestal mode
        #python3 network_single_chip_pedestal.py --pacman_tile 1,2,3,4,5,6,7,8
        echo "Pedestal mode script"

        # Run baseline collection script
        #python3 measure_baseline.py --daq 600 --outloc 2
        echo "Baseline collection script (10 min)"

        # Check for failure
        #python3 failure_check.py
        echo -e "Failure check script\n"

        sleep 60

    fi 

done
