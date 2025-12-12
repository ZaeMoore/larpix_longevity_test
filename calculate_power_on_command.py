"""
Calculate power_on.py command for healthy tiles
==============================================
Authors: Marina Reggiani-Guzzo, Zae Moore (Syracuse University)
Last modified: 12-Dec-2025

Description:
This script calculates the necessary applied --vdda and --vddd for a desired readout
VDDA and VDDD, which are the values provided by the Berkeley lab team for the test
"""

def main(healthy, mode):
    """
    Main function to calculate power_on.py command parameters

    Parameters
    ----------
    healthy : array
        Array of healthy tile numbers
    mode : str
        'nominal' for nominal voltage settings
        'accelerated' for accelerated voltage settings

    Returns
    -------
    string_tile_number : str
        Comma-separated string of tile numbers
    string_vdda : str
        Comma-separated string of vdda values
    string_vddd : str
        Comma-separated string of vddd values
    """

    if mode == 'nominal':
        string_tile_number = ''
        string_vdda = '5243'
        string_vddd = '26214'

        for index, tile_number in enumerate(healthy):
            string_tile_number += f'{list_tiles[index][0]},'

        return string_tile_number[:-1], string_vdda, string_vddd
    
    if mode == 'accelerated':

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

        def calc_vddd(VDDD):
            return ((VDDD-0.2)/2.5) * 65536

        def calc_vdda(VDDA):
            return ((VDDA-2.3)/2.5) * 65536

        list_tile_number = []
        list_vdda = []
        list_vddd = []
        string_tile_number = ''
        string_vdda = ''
        string_vddd = ''

        for index, tile_number in enumerate(healthy):
            # Array format
            list_tile_number.append(list_tiles[index][0])
            list_vdda.append(calc_vdda(list_tiles[index][1]))
            list_vddd.append(calc_vddd(list_tiles[index][2]))
            # String format
            string_tile_number += f'{list_tiles[index][0]},'
            string_vdda += f'{int(calc_vdda(list_tiles[index][1]))},'
            string_vddd += f'{int(calc_vddd(list_tiles[index][2]))},'

        return string_tile_number[:-1], string_vdda[:-1], string_vddd[:-1]


        