import requests
import json

class MESO:
    def __init__(self, token):
        self.base_url = 'https://api.synopticdata.com/v2/'

        self.token = {'token': token}

    def call_api(self, request, params):
        s = requests.Session()
        url = self.base_url + request
        params.update(self.token)
        p = requests.Request('GET', url, params=params).prepare()
        print(p.url)
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

    def get_station_metadata(self, **kwargs):
        req_type = 'stations/metadata'
        return self.call_api(req_type, kwargs)

    def get_timeseries(self, **kwargs):
        req_type = 'stations/timeseries'
        return self.call_api(req_type, kwargs)

class MesoWeatherData:
    RainName = 'precip_accum_24_hour'
    HighTempName = 'air_temp_high_24_hour'
    MinTempName = 'air_temp_low_24_hour'
    SnowName = 'snow_accume_24_hour'
    SnowDepthName = 'snow_depth'

    def __init__(self, meso_api_token):
        self.meso_api = MESO(meso_api_token)
        self.wvars='precip_accum_24_hour,air_temp_high_24_hour,air_temp_low_24_hour,snow_accume_24_hour,snow_depth'

    def get_weather_data_from_stations(self, stations, start_date, end_date):

        station_list = ','.join([s['id'] for s in stations])

        start = start_date.strftime("%Y%m%d0000")
        end = end_date.strftime("%Y%m%d2359")
        print(start)
        print(end)

        # d = self.meso_api.get_timeseries(start=start, end=end, stid=station_list, vars=self.wvars, units='english')
        d = self.meso_api.get_timeseries(start=start, end=end, stid=station_list, units='english')

        print(json.dumps(d, indent=4, sort_keys=True))
        # print d['QC_SUMMARY']
        # print d['SUMMARY']
        # print d['UNITS']

        # for s in d['STATION']:
        #     print 
        #     print(json.dumps(s, indent=4, sort_keys=True))

        return d


