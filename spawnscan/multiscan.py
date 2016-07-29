import time
import json
import multiprocessing
import traceback
import Queue
from ctypes import c_int
from s2sphere import CellId, LatLng
from pgoapi import PGoApi
import spawnscan.stepcalculator as stepcalc


TIMESTAMP = 0
SPAWN_DURATION = 900000  # In milliseconds
THROTTLE = 0.18


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

        # Cleanup and throttle on success
        with scanner.counter_lock:
            scanner.counter.value += 1
        time.sleep(THROTTLE)
    except Exception:
        scanner.queue.put(position)
        if response_dict['status_code'] != 1:
            print('[{}][Invalid status_code: {}] position: {}'.format(multiprocessing.current_process().name, response_dict['status_code'], position))
        else:
            print('[{}][General Exception] position: {}'.format(multiprocessing.current_process().name, position))
            traceback.print_exc()
            print(response_dict)

    # In any case, return the empty list or hopefully list of found pokemon
    return pokemon


def scanner_init(user_queue, queue, counter, counter_lock, retry=0.5):
    scanner.queue = queue
    scanner.counter = counter
    scanner.counter_lock = counter_lock
    api = PGoApi()
    user = user_queue.get()
    api_logged_in = False
    while not api_logged_in:
        print('Attempting to log in user: {}'.format(user[1]))
        api_logged_in = api.login(*user)
        if not api_logged_in:
            print('Failure to log in. Retrying in {} seconds'.format(retry))
            time.sleep(retry)
    scanner.api = api


def iterqueue(items, queue, counter):
    item_count = len(items)
    for item in items:
        queue.put(item)
    while counter.value != item_count:
        try:
            yield queue.get(False)
        except Queue.Empty:
            pass


def pool_scan(users, position_list):
    # Create the Pool
    queue = multiprocessing.Queue()
    user_queue = multiprocessing.Queue()
    for user in users:
        user_queue.put(
            (user['auth_service'], user['username'], user['password'])
        )
    counter = multiprocessing.Value(c_int)
    counter_lock = multiprocessing.Lock()
    init_args = (user_queue, queue, counter, counter_lock)
    pool = multiprocessing.Pool(
        processes=len(users),
        initializer=scanner_init,
        initargs=init_args
    )

    spawns = {}
    for scanned in pool.imap_unordered(scanner, iterqueue(position_list, queue, counter)):
        for found in scanned:
            spawns[found['sid']] = found
    return spawns


def main():

    # Create config
    with open('./config.json') as config_file:
        config = json.load(config_file)

    scan_positions = []
    for rect in config['work']:
        scan_positions += stepcalc.hex_grid(*rect)

    start_time = time.time()  # Right now only want to record actual scanning time (not setup)
    spawns = pool_scan(
        config['users'],
        scan_positions
    )

    print(
        'Found {} spawns in {} seconds!'.format(
            len(spawns), time.time() - start_time
        )
    )

if __name__ == '__main__':
    main()
