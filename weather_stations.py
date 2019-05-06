import noaa_api
import my_utils
import uuid

# using geojson 2.4.1
import geojson
import json

class StationGenerator:
    def __init__(self, noaa_api_token, datasets='GHCND'):
        self.noaa_api = noaa_api.NOAA(noaa_api_token)
        self.datasets=datasets
        self.station_list = []

    def _get_min_max(self, lat_long_list):
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

    def _meets_min_distance(self, location, coord_list, min_distance):
        this_lat = location['latitude']
        this_long = location['longitude']
        for i in coord_list:
            d = my_utils.distance(this_lat, this_long, i['lat'], i['long'])
            if d <= min_distance:
                return True
        return False

    def _fix_extent(self, min_coord, max_coord, min_distance):

        # Not perfect, but treet this as effectively "diameter of circle"
        d = (my_utils.distance(min_coord['lat'], min_coord['long'],
                max_coord['lat'], max_coord['long'])/2)

        delta = min_distance - d
        if delta < 0:
            return

        factor = ((min_distance-d)/ d)/100

        min_coord['lat']  -= min_coord['lat']* (factor/10)
        min_coord['long'] += min_coord['long']*(factor/10)
        max_coord['lat']  += max_coord['lat']* (factor/10)
        max_coord['long'] -= max_coord['long']*(factor/10)

        d2 = my_utils.distance(min_coord['lat'], min_coord['long'],
                max_coord['lat'], max_coord['long'])

        return min_coord, max_coord

    def generate_station_list(self, coord_list, min_distance):

        min_coord, max_coord = self._get_min_max(coord_list)

        min_coord, max_coord = self._fix_extent(min_coord, max_coord, min_distance)
        extent= "%s, %s, %s, %s" % (min_coord['lat'],
                min_coord['long'],
                max_coord['lat'],
                max_coord['long'])

        steps = 10
        offset = 0
        while True:
            locations = self.noaa_api.get_stations(
                    extent=extent,
                    datasets=self.datasets,
                    limit=steps,
                    offset=offset,
                    units='standard')
            if locations is None:
                break
            for i in locations:
                if self._meets_min_distance(i, coord_list, min_distance):
                    #convert meters to feet if applicable
                    if 'eleveationUnit' in i.keys() and i['elevationUnit'] == 'METERS':
                        m = float(i['elevation'])
                        f = my_utils.meters_to_feet(m)
                        i['elevation'] = str(f)
                        i['elevationUnit'] = 'FEET'
                    self.station_list.append(i)
            if len(locations) <= 0:
                break
            offset += len(locations)

    def write_features_to_file(self, filename):
        features = []

        fold_id = str(uuid.uuid1())
        folder = geojson.Feature(
                properties={"class": "Folder", "title": "weather"},
                id=fold_id)
        features.append(folder)

        base_properties = {"class" : "Marker", "marker-color": "#00FFFF", "marker-symbol": "point", "folderId" : fold_id}

        for s in self.station_list:
            point = geojson.Point(( s['longitude'], s['latitude'],0,0 ))
            uid = str(uuid.uuid1())

            extended_properties={"title" : s['name'], "description" : str(s)}
            properties = dict(extended_properties, **base_properties)

            f = geojson.Feature(geometry=point, properties=properties, id=uid)

            features.append(f)

        feature_collection = geojson.FeatureCollection(features)
        with open(filename, "w") as out_file:
            out_file.write(geojson.dumps(feature_collection))

