import json
import math
import os
import logging
import time
from six.moves import range
import geojson

import threading

from pgoapi import PGoApi
from pgoapi.utilities import f2i

from s2sphere import CellId, LatLng


TIMESTAMP = 0
OUTPUT_DIR = 'output'
POKES = 'pokes'
SPAWNS = 'spawns'
STOPS = 'stops'
GYMS = 'gyms'


map_objects = {
    POKES: {},
    SPAWNS: {},
    STOPS: {},
    GYMS: {},
}

scans = []

# Config file
with open('config.json') as config_file:
    config = json.load(config_file)


def get_cellid(lat, lng, level=15):
    origin = CellId.from_lat_lng(LatLng.from_degrees(lat, lng)).parent(level)
    walk = [origin.id()]

    # 10 before and 10 after
    next = origin.next()
    prev = origin.prev()
    for i in range(10):
        walk.append(prev.id())
        walk.append(next.id())
        next = next.next()
        prev = prev.prev()
    return sorted(walk)


def doScan(sLat, sLng, api):
    api.set_position(sLat, sLng, 0)
    cellids = get_cellid(sLat, sLng)
    api.get_map_objects(
        latitude=f2i(sLat),
        longitude=f2i(sLng),
        since_timestamp_ms=[TIMESTAMP] * len(cellids),
        cell_id=cellids
    )
    response_dict = api.call()
    try:
        cells = response_dict['responses']['GET_MAP_OBJECTS']['map_cells']
    except (TypeError, KeyError):
        print('error getting map data for {}, {}'.format(sLat, sLng))
        return
    for cell in cells:
        # print(cell['s2_cell_id'])
        curTime = cell['current_timestamp_ms']
        if 'wild_pokemons' in cell:
            for wild in cell['wild_pokemons']:
                if wild['time_till_hidden_ms'] > 0:
                    timeSpawn = (curTime + (wild['time_till_hidden_ms'])) - 900000
                    gmSpawn = time.gmtime(int(timeSpawn / 1000))
                    secSpawn = (gmSpawn.tm_min * 60) + (gmSpawn.tm_sec)
                    phash = '{},{}'.format(timeSpawn, wild['spawn_point_id'])
                    shash = '{},{}'.format(secSpawn, wild['spawn_point_id'])
                    pokeLog = {
                        'time': timeSpawn,
                        'sid': wild['spawn_point_id'],
                        'lat': wild['latitude'],
                        'lng': wild['longitude'],
                        'pid': wild['pokemon_data']['pokemon_id'],
                        'cell': CellId.from_lat_lng(LatLng.from_degrees(wild['latitude'], wild['longitude'])).to_token()
                    }
                    spawnLog = {
                        'time': secSpawn,
                        'sid': wild['spawn_point_id'],
                        'lat': wild['latitude'],
                        'lng': wild['longitude'],
                        'cell': CellId.from_lat_lng(LatLng.from_degrees(wild['latitude'], wild['longitude'])).to_token()
                    }
                    map_objects[POKES][phash] = pokeLog
                    map_objects[SPAWNS][shash] = spawnLog
        if 'forts' in cell:
            for fort in cell['forts']:
                if fort['enabled']:
                    if 'type' in fort:
                        # Got a pokestop
                        stopLog = {
                            'id': fort['id'],
                            'lat': fort['latitude'],
                            'lng': fort['longitude'],
                            'lure': -1
                        }
                        if 'lure_info' in fort:
                            stopLog['lure'] = fort['lure_info']['lure_expires_timestamp_ms']
                        map_objects[STOPS][fort['id']] = stopLog
                    if 'gym_points' in fort:
                        gymLog = {
                            'id': fort['id'],
                            'lat': fort['latitude'],
                            'lng': fort['longitude'],
                            'team': 0
                        }
                        if 'owned_by_team' in fort:
                            gymLog['team'] = fort['owned_by_team']
                        map_objects[GYMS][fort['id']] = gymLog


def genwork():
    totalwork = 0
    for rect in config['work']:
        dlat = 0.6 * 0.00225
        dlng = dlat / math.cos(math.radians((rect[0] + rect[2]) * 0.5))
        startLat = rect[2] + (0.624 * dlat)
        startLng = rect[1] + (0.624 * dlng)
        latSteps = int((((rect[0] - rect[2])) / dlat) + 0.75199999)
        if latSteps < 1:
            latSteps = 1
        lngSteps = int((((rect[3] - rect[1])) / dlng) + 0.75199999)
        if lngSteps < 1:
            lngSteps = 1
        for i in range(latSteps):
            for j in range(lngSteps):
                scans.append([startLat + (dlat * i), startLng + (dlng * j)])
        totalwork += latSteps * lngSteps
    return totalwork


def worker(wid, Tthreads):
    workStart = int((wid * len(scans)) / Tthreads)
    workStop = int(((wid + 1) * len(scans)) / Tthreads)
    print('worker {} is doing steps {} to {}'.format(wid, workStart, workStop))
    # Login
    api = PGoApi()
    api.set_position(0, 0, 0)
    if not api.login(
            config['auth_service'],
            config['users'][wid]['username'],
            config['users'][wid]['password']):
        print('worker {} unable to log in'.format(wid))
        return
    # Iterate
    startTime = time.time()
    print('worker {} is doing first pass'.format(wid))
    for i in range(workStart, workStop):
        doScan(scans[i][0], scans[i][1], api)
    curTime = time.time()
    print('worker {} took {} secconds to do first pass now sleeping for {}'.format(wid, curTime - startTime, 600 - (curTime - startTime)))
    time.sleep(600 - (curTime - startTime))
    print('worker {} is doing second pass'.format(wid))
    for i in range(workStart, workStop):
        doScan(scans[i][0], scans[i][1], api)
    curTime = time.time()
    print('worker {} took {} secconds to do second pass now sleeping for {}'.format(wid, curTime - startTime, 1200 - (curTime - startTime)))
    time.sleep(1200 - (curTime - startTime))
    print('worker {} is doing third pass'.format(wid))
    for i in range(workStart, workStop):
        doScan(scans[i][0], scans[i][1], api)
    curTime = time.time()
    print('worker {} took {} secconds to do third  pass now sleeping for {}'.format(wid, curTime - startTime, 1800 - (curTime - startTime)))
    time.sleep(1800 - (curTime - startTime))
    print('worker {} is doing forth pass'.format(wid))
    for i in range(workStart, workStop):
        doScan(scans[i][0], scans[i][1], api)
    curTime = time.time()
    print('worker {} took {} secconds to do fourth pass now sleeping for {}'.format(wid, curTime - startTime, 2400 - (curTime - startTime)))
    time.sleep(2400 - (curTime - startTime))
    print('worker {} is doing fith pass'.format(wid))
    for i in range(workStart, workStop):
        doScan(scans[i][0], scans[i][1], api)
    curTime = time.time()
    print('worker {} took {} secconds to do fith pass now sleeping for {}'.format(wid, curTime - startTime, 3000 - (curTime - startTime)))
    time.sleep(3000 - (curTime - startTime))
    print('worker {} is doing sixth pass'.format(wid))
    for i in range(workStart, workStop):
        doScan(scans[i][0], scans[i][1], api)
    curTime = time.time()
    print('worker {} took {} secconds to do sixth pass'.format(wid, curTime - startTime))


def main():
    tscans = genwork()
    print('total of {} steps, approx {} seconds for scan'.format(tscans, tscans / (4.5 * len(config['users']))))
    if (tscans / (4.5 * len(config['users']))) > 600:
        print('error. scan will take more than 10mins so all 6 scans will take more than 1 hour')
        print('please try scanning a smaller area')
        return
    # Heres the logging setup
    # log settings
    # log format
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')
    # log level for http request class
    log = logging.getLogger("requests").setLevel(logging.WARNING)
    # log level for main pgoapi class
    log = logging.getLogger("pgoapi").setLevel(logging.WARNING)
    # log level for internal pgoapi class
    log = logging.getLogger("rpc_api").setLevel(logging.WARNING)

    if config['auth_service'] not in ['ptc', 'google']:
        log.error("Invalid Auth service specified! ('ptc' or 'google')")
        return None

    # Setup done

    # Output
    threads = []
    for user in config['users']:
        t = threading.Thread(
            target=worker,
            args=(len(threads), len(config['users']))
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    print('all done. saving data')

    # Raw map object output
    for obj_type, obj_dict in map_objects.iteritems():
        list(obj_dict.values())
        with open(os.path.join(OUTPUT_DIR, '{}.json'.format(obj_type)), 'w') as obj_file:
            json.dump(list(obj_dict.values()), obj_file)

    # Output GeoJSON data
    # These map object types should be GeoJSON encoded
    GEO_JSON_KEYS = (GYMS, STOPS)
    for geo_key in GEO_JSON_KEYS:
        geopoints = []
        for location in list(map_objects[geo_key].values()):
            point = geojson.Point((location['lng'], location['lat']))
            feature = geojson.Feature(
                geometry=point,
                id=location['id'],
                properties={"name": location['id']}
            )
            geopoints.append(feature)
        with open(os.path.join(OUTPUT_DIR, 'geo_{}.json'.format(geo_key)), 'w') as geo_file:
            json.dump(geojson.FeatureCollection(geopoints), geo_file)
