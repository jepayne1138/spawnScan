import time
import json
import multiprocessing
import traceback
from s2sphere import CellId, LatLng
from pgoapi import PGoApi
import spawnscan.stepcalculator as stepcalc


TIMESTAMP = 0
SPAWN_DURATION = 900000  # In milliseconds


def get_cellid(lat, lng, level=15):
    origin = CellId.from_lat_lng(
        LatLng.from_degrees(lat, lng)
    ).parent(level)
    return origin.id()


def scanner(position):
    print('[{}]Scanning position: {}'.format(multiprocessing.current_process().name, position))

    api = scanner.api

    pokemon = []

    try:
        lat, lng, alt = position
        cellid = get_cellid(lat, lng)
        api.set_position(lat, lng, alt)

        api.get_map_objects(
            latitude=lat,
            longitude=lng,
            since_timestamp_ms=TIMESTAMP,
            cell_id=cellid
        )
        response_dict = api.call()
        cell = response_dict['responses']['GET_MAP_OBJECTS']['map_cells'][0]

        # Parse return value of the cell
        cur_time = cell['current_timestamp_ms']
        if 'wild_pokemons' in cell:
            for wild in cell['wild_pokemons']:
                # Get spawn time
                time_spawn = (cur_time + (wild['time_till_hidden_ms'])) - SPAWN_DURATION
                pokemon.append({
                    'time': time_spawn,
                    'sid': wild['spawn_point_id'],
                    'lat': wild['latitude'],
                    'lng': wild['longitude'],
                    'pid': wild['pokemon_data']['pokemon_id'],
                })

    except Exception:  # TODO catch specific errors
        traceback.print_exc()
        # print('Error getting map data for {}, {}'.format(lat, lng))
    return pokemon


def scanner_init(auth, user, password):
    api = PGoApi()
    while not api.login(auth, user, password):
        print('Failure to log in. Retrying in 5 seconds')
        time.sleep(5)
    scanner.api = api


def pool_scan(auth, username, password, position_list, processes=None):
    # Create the Pool
    init_args = (auth, username, password)
    pool = multiprocessing.Pool(initializer=scanner_init, initargs=init_args)

    spawns = {}
    for scanned in pool.imap_unordered(scanner, position_list):
        for found in scanned:
            spawns[found['sid']] = found
    return spawns


def main():
    start_time = time.time()

    # Create config
    with open('../config.json') as config_file:
        config = json.load(config_file)

    scan_positions = []
    for rect in config['work']:
        scan_positions += stepcalc.hex_grid(*rect)

    spawns = pool_scan(
        config['auth_service'],
        config['users'][0]['username'],
        config['users'][0]['password'],
        scan_positions
    )

    print(
        'Found {} spawns in {} seconds!'.format(
            len(spawns), time.time() - start_time
        )
    )

if __name__ == '__main__':
    main()
