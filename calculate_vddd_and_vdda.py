
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

for tile_info in list_tiles:
    list_tile_number = list_tile_number + f"{tile_info[0]}" + ","    
    list_vdda = list_vdda + f"{calc_vdda(tile_info[1]):.0f}" + ","
    list_vddd = list_vddd + f"{calc_vddd(tile_info[2]):.0f}" + ","

# remove last ','
list_tile_number = list_tile_number[:-1]
list_vdda = list_vdda[:-1]
list_vddd = list_vddd[:-1]

print(f'python3 power_on.py --pacman_tile {list_tile_number} --vdda {list_vdda} --vddd {list_vddd}')
