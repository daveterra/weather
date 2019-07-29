import noaa_api
import meso_api
import my_utils
import uuid

# using geojson 2.4.1
import geojson
import json

class StationGenerator:
    def __init__(self, noaa_api_token, meso_api_token):
        self.noaa_api = noaa_api.NOAA(noaa_api_token)
        self.meso_api = meso_api.MESO(meso_api_token)
        self.noaa_datasets='GHCND'
        # self.meso_vars='air_temp,snow_depth,'
        # self.meso_vars=
        self.station_list = []

    def _meets_min_distance(self, location, coord_list, min_distance):
        this_lat  = location['lat']
        this_long = location['long']
        for i in coord_list:
            d = my_utils.distance(this_lat, this_long, i['lat'], i['long'])
            if d <= min_distance:
                return True
        return False

    def _get_extent(self, lat_long_list, min_distance):
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

        # Not perfect, but treet this as effectively "diameter of circle"
        d = (my_utils.distance(min_coord['lat'], min_coord['long'],
                max_coord['lat'], max_coord['long'])/2)

        delta = min_distance - d
        if delta > 0:
            factor = ((min_distance-d)/ d)/100
            min_coord['lat']  -= min_coord['lat']* (factor/10)
            min_coord['long'] += min_coord['long']*(factor/10)
            max_coord['lat']  += max_coord['lat']* (factor/10)
            max_coord['long'] -= max_coord['long']*(factor/10)

        return min_coord, max_coord

    def _get_noaa_stations(self, min_coord, max_coord):
        steps = 10
        offset = 0
        extent= "%s,%s,%s,%s" % (min_coord['lat'],
                min_coord['long'],
                max_coord['lat'],
                max_coord['long'])

        while True:
            locations = self.noaa_api.get_stations(
                    extent=extent,
                    datasets=self.noaa_datasets,
                    limit=steps,
                    offset=offset,
                    units='standard')
            if locations is None:
                break
            for l in locations:
                #convert meters to feet if applicable
                new_location = {}
                new_location['api']  = 'NOAA'
                new_location['name'] = l['name']
                new_location['id']   = l['id']
                new_location['lat']  = float(l['latitude'])
                new_location['long'] = float(l['longitude'])

                if 'eleveationUnit' in l.keys() and l['elevationUnit'] == 'METERS':
                    m = float(l['elevation'])
                    f = my_utils.meters_to_feet(m)
                    new_location['elevation'] = int(f)
                else:
                    new_location['elevation'] = int(l['elevation'])
                self.station_list.append(new_location)
            if len(locations) <= 0:
                break
            offset += len(locations)

    def _get_meso_stations(self, min_coord, max_coord):
        bbox = "%s,%s,%s,%s" % (min_coord['long'],
                min_coord['lat'],
                max_coord['long'],
                max_coord['lat'])
        locations = self.meso_api.get_station_metadata(bbox=bbox)
        print bbox
        print len(locations['STATION'])
        for l in locations['STATION']:
            new_location = {}
            new_location['api']  = 'MESO'
            new_location['name'] = l['NAME']
            new_location['id']   = l['STID']
            new_location['lat']  = float(l['LATITUDE'])
            new_location['long'] = float(l['LONGITUDE'])
            new_location['elevation'] = int(l['ELEVATION'])
            self.station_list.append(new_location)

    def generate_station_list(self, coord_list, min_distance):

        min_coord, max_coord = self._get_extent(coord_list, min_distance)
        self._get_noaa_stations(min_coord, max_coord)
        # self._get_meso_stations(min_coord, max_coord)

        dupes = set()
        for s in self.station_list:
            if not self._meets_min_distance(s, coord_list, min_distance):
                self.station_list.remove(s)

        #TODO: De-dupe?

    def write_features_to_file(self, filename):
        features = []

        fold_id = str(uuid.uuid1())
        folder = geojson.Feature(
                properties={"class": "Folder", "title": "weather"},
                id=fold_id)
        features.append(folder)

        base_properties = {"class" : "Marker", "marker-color": "#00FFFF", "marker-symbol": "point", "folderId" : fold_id}

        for s in self.station_list:
            point = geojson.Point(( s['long'], s['lat'],0,0 ))
            uid = str(uuid.uuid1())

            extended_properties={"title" : s['name'], "description" : str(s)}
            properties = dict(extended_properties, **base_properties)

            f = geojson.Feature(geometry=point, properties=properties, id=uid)

            features.append(f)

        feature_collection = geojson.FeatureCollection(features)
        with open(filename, "w") as out_file:
            out_file.write(geojson.dumps(feature_collection))

