import requests

class NOAA:
    def __init__(self, token):
        self.base_url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/'
        self.token = {'token': token}

    def call_api(self, request, params):
        s = requests.Session()
        url = self.base_url + request
        p = requests.Request('GET', url, headers=self.token, params=params).prepare()
        r = s.send(p)

        if not r.ok:
            print("Error: " + str(r.status_code))
            print(r.content)
            return None
        else:
            r = r.json()
            if 'results' not in r: 
                return r
            return r['results']

    def get_datasets(self, **kwargs):
        req_type = 'datasets'
        return self.call_api(req_type, kwargs)

    def get_datasets_with_id(self, which_id, **kwargs):
        req_type = 'datasets/' + which_id
        return self.call_api(req_type, kwargs)

    def get_data_categories(self, **kwargs):
        req_type = 'datacategories'
        return self.call_api(req_type, kwargs)

    def get_data_categories_with_id(self, which_id, **kwargs):
        req_type = 'datacategories/' + which_id
        return self.call_api(req_type, kwargs)

    def get_data_types(self, **kwargs):
        req_type = 'datatypes'
        return self.call_api(req_type, kwargs)

    def get_data_types_by_id(self, which_id, **kwargs):
        req_type = 'datatypes/' + which_id
        return self.call_api(req_type, kwargs)

    def get_location_categories(self, **kwargs):
        req_type = 'locationcategories'
        return self.call_api(req_type, kwargs)

    def get_location_categories_with_id(self, which_id, **kwargs):
        req_type = 'locationcategories/' + which_id
        return self.call_api(req_type, kwargs)

    def get_locations(self, **kwargs):
        req_type = 'locations'
        return self.call_api(req_type, kwargs)

    def get_locations_with_id(self, which_id, **kwargs):
        req_type = 'locations/' + which_id
        return self.call_api(req_type, kwargs)

    def get_stations(self, **kwargs):
        req_type = 'stations'
        return self.call_api(req_type, kwargs)

    def get_stations_with_id(self, which_id, **kwargs):
        req_type = 'stations/' + which_id
        return self.call_api(req_type, kwargs)

    def get_data(self, dataset_id, **kwargs):
        req_type = 'data?datasetid=' + dataset_id
        return self.call_api(req_type, kwargs)


class NOAAWeatherData:
    def __init__(self, noaa_api_token):
        self.noaa_api = NOAA(noaa_api_token)
        self.dataset='GHCND'
        self.datatypes=['TMIN', 'TMAX', 'TAVG', 'PRCP', 'SNOW', 'SNWD']

    def _get_station_elevations(self, which_station, stations):
        ret = { 'elevation' : 0 }
        for s in stations:
            if s['id'] == which_station:
                ret['elevation'] = s['elevation']
                break

        return ret

    def get_weather_data_from_stations(self, stations, start_date, end_date):
        data = []

        print( start_date)
        print( end_date)

        num_stations = len(stations)
        cur_station_num = 1

        station_ids = []
        # Build station list
        for station in stations:
            station_ids.append(station['id'])

        limit = 10
        offset = 0
        records_appended = 0
        while True:
            d = self.noaa_api.get_data(
                    dataset_id=self.dataset,
                    units='standard',
                    datatypeid=self.datatypes,
                    stationid=station_ids,
                    startdate=start_date,
                    enddate=end_date,
                    sortfield='date',
                    sortorder='desc',
                    limit=limit,
                    offset=offset)
            if d is None:
                print("\tRequest failed, retrying")
                continue

            if len(d) <= 0:
                break
            for i in d:
                i.update(self._get_station_elevations(i['station'], stations))
                records_appended += 1
                data.append(i)
            offset += len(d)
        return data

