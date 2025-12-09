# Author: Marina Reggiani-Guzzo (Syracuse University)
# Last modified: 9-Dec-2025

# Description: 
# This script calculates the necessary applied --vdda and --vddd for a desired readout 
# VDDA and VDDD, which are the values provided by the Berkeley lab team for the test.

# Output:
# Print statement with the full power_on.py command. This should help avoiding typos
# when actually running the command on the terminal.

# How to run:
# > python3 calculate_vddd_and_vdda.py --healthy $healthy_tiles

# Flag options:
# --healthy: list of healthy tiles as --healthy 1 2 3 4 5

import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--healthy', type=str, help='List of healthy pacman tiles')
    args = parser.parse_args()

    # list of [tile,vdda,vddd]
    list_tiles = [
        [1, 2.5, 1.2],
        [2, 2.9, 1.38],
        [3, 2.9, 1.38],
        [4, 3.2, 1.55],
        [5, 3.2, 1.55],
        [6, 3.6, 1.73],
        [7, 3.6, 1.73],
        [8, 3.6, 1.73]
    ]

    # ===================================================================

    def calc_vddd(VDDD):
        return ((VDDD-0.2)/2.5) * 65536

    def calc_vdda(VDDA):
        return ((VDDA-2.3)/2.5) * 65536

    list_tile_number = ''
    list_vdda = ''
    list_vddd = ''

    for tile_number in args.healthy.split(" "):
        nentry = int(tile_number) - 1
        list_tile_number = list_tile_number + f"{list_tiles[nentry][0]}" + ","    
        list_vdda = list_vdda + f"{calc_vdda(list_tiles[nentry][1]):.0f}" + ","
        list_vddd = list_vddd + f"{calc_vddd(list_tiles[nentry][2]):.0f}" + ","

    # remove last ','
    list_tile_number = list_tile_number[:-1]
    list_vdda = list_vdda[:-1]
    list_vddd = list_vddd[:-1]

    print(f'python3 power_on.py --pacman_tile {list_tile_number} --vdda {list_vdda} --vddd {list_vddd}')