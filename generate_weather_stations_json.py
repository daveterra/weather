import config
import noaa_api

import json
import uuid
import my_utils

# using geojson 2.4.1
import geojson

dataset='GHCND'
# dataset='GSOM'

input_file='/Users/dave/Downloads/Hat_Creek_Rim_.json'
output_file="Hat_Creek_RIM_weather.json"
# input_file='/Users/dave/Downloads/JMT.json'
# output_file="JMT_weather.json"

def get_lat_long_from_file_old(file_name):
    final_list = []
    with open(file_name) as json_file:
        coords = []
        id = 'coordinates'

        def _decode_dict(a_dict):
            try: coords.append(a_dict[id])
            except KeyError: pass
            return a_dict

        json.load(json_file, object_hook=_decode_dict)  # Return value ignored.

        def get_lat_long(l, ret):
            if(type(l[0]) == list):
                for i in l:
                    get_lat_long(i, ret)
            elif(type(l[0]) == float):
                ret.append({"lat": l[1], "long": l[0]})

        get_lat_long(coords, final_list)
    return final_list


def get_lat_long_from_file(file_name):

    final_list = []
    with open(file_name) as json_file:

        feature_collection = geojson.load(json_file)
        coords = list(geojson.utils.coords(feature_collection))

        for x in coords:
            final_list.append({"lat" : x[1], "long" : x[0]})

        return final_list

def get_min_max(lat_long_list):
    max_coord = {"lat": -999, "long": -999}
    min_coord = {"lat": 999, "long": 999}

    for i in lat_long_list:
        if i['lat'] > max_coord['lat']:
            max_coord['lat'] = i['lat']
        elif i['long'] > max_coord['long']:
            max_coord['long'] = i['long']

        if i['lat'] < min_coord['lat']:
            min_coord['lat'] = i['lat']
        elif i['long'] < min_coord['long']:
            min_coord['long'] = i['long']

    return min_coord, max_coord

def meets_min_distance(location, coord_list, min_distance):
    this_lat = location['latitude']
    this_long = location['longitude']
    for i in coord_list:
        d = my_utils.distance(this_lat, this_long, i['lat'], i['long'])
        if d <= min_distance:
            return True
    return False

def generate_station_list(min_coord, max_coord, noaa, coord_list, min_distance=10):
    ret = []
    extent= "%s, %s, %s, %s" % (min_coord['lat'],
            min_coord['long'],
            max_coord['lat'],
            max_coord['long'])
    steps = 10
    offset = 0
    while True:
        locations = noaa.get_stations(
                extent=extent,
                datasets=dataset,
                limit=steps,
                offset=offset,
                units='standard')
        if locations is None:
            break
        for i in locations:
            if meets_min_distance(i, coord_list, min_distance):
                #convert meters to feet if applicable
                if i['elevationUnit'] == 'METERS':
                    m = float(i['elevation'])
                    f = (m / .3048)
                    i['elevation'] = str(f)
                    i['elevationUnit'] = 'FEET'
                ret.append(i)
        if len(locations) <= 0:
            break
        offset += len(locations)

    return ret

def write_features_to_file(stations, filename):
    features = []

    fold_id = str(uuid.uuid1())
    folder = geojson.Feature(
            properties={"class": "Folder", "title": "weather"},
            id=fold_id)
    features.append(folder)

    base_properties = {"class" : "Marker", "marker-color": "#00FFFF", "marker-symbol": "point", "folderId" : fold_id}

    for s in stations:
        point = geojson.Point(( s['longitude'], s['latitude'],0,0 ))
        uid = str(uuid.uuid1())

        extended_properties={"title" : s['name'], "description" : str(s)}
        properties = dict(extended_properties, **base_properties)

        f = geojson.Feature(geometry=point, properties=properties, id=uid)

        features.append(f)

    feature_collection = geojson.FeatureCollection(features)
    with open(filename, "w") as out_file:
        out_file.write(geojson.dumps(feature_collection))


def main():
    print "Reading file \'%s\'"  % (input_file)
    lat_long_list = get_lat_long_from_file(input_file)

    min_coord, max_coord = get_min_max(lat_long_list)

    noaa = noaa_api.noaa_api(config.noaa_api_token)
    print noaa
    stations = generate_station_list(min_coord, max_coord, noaa, lat_long_list)
    print "Retrieved %d stations" % (len(stations))

    print "Writing filtered results to \'%s\'" % (output_file)
    write_features_to_file(stations, output_file)

main()
