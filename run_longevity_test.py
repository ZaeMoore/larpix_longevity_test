"""
LarPix Longevity Test Script
===========================
Author: Zae Moore (Syracuse University)
Last modified: 12-Dec-2025

Description:
This script runs the longevity test for LArPix boards by alternating between
nominal voltage data collection and accelerated-voltage baseline collection.
It monitors the health of the boards and adjusts the test parameters accordingly.
"""
import os
import time
import subprocess
from datetime import datetime
import failure_test
import calculate_power_on_command
import monitor_larpix_readout

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def now_day():
    """
    Returns the current day in YYYY-MM-DD format
    """
    return datetime.now().strftime("%Y-%m-%d")

def now_time():
    """
    Returns the current time in HH-MM format
    """
    return datetime.now().strftime("%H:%M")

def minutes_since_midnight(timestr):
    """
    Converts a time string "HH:MM" to minutes since midnight
    """
    h, m = map(int, timestr.split(":"))
    return h * 60 + m

def run(cmd):
    """
    Runs a shell command and checks for errors
    """
    print("Running:", cmd)
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed: {cmd}")
    return result.returncode


# ------------------------------------------------------------
# Initial setup
# ------------------------------------------------------------

current_day = now_day()
current_time = now_time()
t0 = current_time        # Time of first step-1 run
d0 = current_day         # Day script started

# Seconds since last step 1
seconds_since_step1 = 0
last_step1_time = time.time()

# Convert t0 to minutes
t0_minutes = minutes_since_midnight(t0)

print(f"Starting longevity test script.\nStart day d0 = {current_day}. Start time t0 = {current_time}.\n")

# Initial time in seconds for week 0
w0_s = int(time.time())
directory = f"output_data/su_cryolongevity_{current_day}"
os.makedirs(directory, exist_ok=True)

# Change to location of your baseline file
baseline_file = "baseline_files/baseline_2025_12_09_10_27_51.json"

# Running tiles
healthy_tiles = [1,2,3,4,5,6,7,8]
#healthy_tiles_str = ' '.join(str(tile) for tile in healthy_tiles)
#healthy_tiles_com = ','.join(str(tile) for tile in healthy_tiles)

# ------------------------------------------------------------
# Main infinite loop
# ------------------------------------------------------------

while True:

    current_day = now_day()
    current_time = now_time()
    print(f"\n\nCurrent day: {current_day}. Current time: {current_time}.")

    current_minutes = minutes_since_midnight(current_time)
    print(f"Step 1 runs at time t0 = {t0}")

    time_difference = current_minutes - t0_minutes
    print(f"Current time - t0 difference in minutes: {time_difference}")

    seconds_since_step1 = int(time.time() - last_step1_time)
    print(f"Seconds since step 1 last finished: {seconds_since_step1}\n")

    # --------------------------------------------------------
    # Step 1: If current time t−t0 < 10 min
    # --------------------------------------------------------
    if 0 <= time_difference <= 10:
        mode = 'nominal'

        # If a week has passed, create a new directory
        week_difference = int(time.time()) - w0_s
        if week_difference > 604800:  # 7 days
            w0_s = int(time.time())
            print("Creating new subdirectory for the week")
            directory = f"su_cryolongevity_{current_day}"
            os.makedirs(directory, exist_ok=True)

        print("Collecting data with nominal voltages")

        # Calculate power_on.py command for healthy tiles
        # calculate_power_on_command
        # Input: healthy tiles [array]
        # Output: list_tile_number, list_vdda, list_vddd [strings with commas]
        print("Power on healthy tiles")
        list_tile_number, list_vdda, list_vddd = calculate_power_on_command.main(healthy_tiles)
        run(f'python3 power_on.py --pacman_tile {list_tile_number} --vdda 5243 --vddd 26214')

        # Set boards to pedestal mode
        print("Set boards to pedestal mode")
        run(f'python3 network_single_chip_pedestal.py --pacman_tile {list_tile_number}')

        # Monitor LArPix readout script
        # Collects data, checks for failure, and returns healthy tiles
        # monitor_larpix_readout
        # Input: healthy tiles [array], baseline_file [string], directory [string], mode [string]
        # Output: healthy tiles [array]
        print("Monitor LArPix readout script")
        healthy_tiles = monitor_larpix_readout.main(healthy_tiles, baseline_file, directory, mode)

        last_step1_time = time.time()

    # --------------------------------------------------------
    # Backup Step 1: If more than 24 hours have passed
    # --------------------------------------------------------
    elif seconds_since_step1 > 86400:
        mode = 'nominal'

        print("Collecting data with nominal voltages")

        # Calculate power_on.py command for healthy tiles
        # calculate_power_on_command
        # Input: healthy tiles [array]
        # Output: list_tile_number, list_vdda, list_vddd [strings with commas]
        print("Power on healthy tiles")
        list_tile_number, list_vdda, list_vddd = calculate_power_on_command.main(healthy_tiles)
        run(f'python3 power_on.py --pacman_tile {list_tile_number} --vdda 5243 --vddd 26214')

        # Set boards to pedestal mode
        print("Set boards to pedestal mode")
        run(f'python3 network_single_chip_pedestal.py --pacman_tile {list_tile_number}')

        # Monitor LArPix readout script
        # Collects data, checks for failure, and returns healthy tiles
        # monitor_larpix_readout
        # Input: healthy tiles [array], baseline_file [string], directory [string]
        # Output: healthy tiles [array]
        print("Monitor LArPix readout script")
        healthy_tiles = monitor_larpix_readout.main(healthy_tiles, baseline_file, directory, mode)

        last_step1_time = time.time()

    # --------------------------------------------------------
    # Step 2: accelerated-voltage baseline collection
    # --------------------------------------------------------
    else:
        mode = 'accelerated'

        print("Collect baseline with accelerated voltages")

        # Calculate power_on.py command for healthy tiles
        print("Power on healthy tiles")
        list_tile_number, list_vdda, list_vddd = calculate_power_on_command.main(healthy_tiles)
        run(f'python3 power_on.py --pacman_tile {list_tile_number} --vdda {list_vdda} --vddd {list_vddd}')

        # Set boards to pedestal mode
        print("Set boards to pedestal mode")
        run(f'python3 network_single_chip_pedestal.py --pacman_tile {list_tile_number}')

        # Monitor LArPix readout script
        # Collects data, checks for failure, and returns healthy tiles
        # monitor_larpix_readout
        # Input: healthy tiles [array], baseline_file [string], directory [string]
        # Output: healthy tiles [array]
        print("Monitor LArPix readout script")
        healthy_tiles = monitor_larpix_readout.main(healthy_tiles, baseline_file, directory, mode)

        last_step1_time = time.time()

    # Sleep a bit to avoid hammering system when testing script
    # time.sleep(60)