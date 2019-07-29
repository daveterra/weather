from dateutil import parser
from datetime import timedelta
from datetime import datetime
from datetime import date

import noaa_api
import meso_api

class WeatherDataset():
    def __init__(self, start_date, end_date, noaa_api_token, meso_api_token):
        self.start_date = start_date
        self.end_date = end_date
        self.noaa_api_token = noaa_api_token
        self.meso_api_token = meso_api_token

        self.datatypes = {
                'min_temp' : { 'noaa' : 'TMIN' },
                'max_temp' : { 'noaa' : 'TMAX' },
                'avg_temp' : { 'noaa' : 'TAVG' },
                'rain' : { 'noaa' : 'PRCP' },
                'snow' : { 'noaa' : 'SNOW' },
                'snow_depth' : { 'noaa' : 'SNWD' },
                }

        self.dataset = {}
        for k in self.datatypes:
            self.dataset[k] = []

    def get_noaa_data_filter(self):
        return [d['noaa'] for k, d in self.datatypes.items()]

    def add_noaa_data(self, data):
        noaa_map = { d['noaa'] : k for k,d in self.datatypes.items()}
        noaa_filter = self.get_noaa_data_filter()
        for d in data:
            if d['datatype'] not in noaa_filter:
                continue
            fixed_date = parser.parse(d['date']).strftime("%Y-%m-%d")
            row = { 'date' : fixed_date,
                    'value' : d['value'],
                    'elevation' : d['elevation'],
                    'station_id': d['station']}
            key = noaa_map[d['datatype']]
            self.dataset[key].append(row)

    def get_data_keys(self):
        return ['date', 'value', 'elevation', 'station_id']

    def get_date_keys(self):
        current_date = self.start_date
        one_day = timedelta(days=1)
        ret = []
        while current_date <= self.end_date:
            ret.append([current_date.strftime("%m-%d")])
            current_date += one_day
        return ret

    def get_data_types(self):
        return [k for k in self.datatypes]

    def get_matrix_for_datatype(self, datatype):
        ret = []
        for row in self.dataset[datatype]:
            ret.append([row[k] for k in self.get_data_keys()])
        return ret

    def get_matrix_for_datatype_averaged(self, datatype):
        # Should return a 1-d matrix (e.g. column)
        current_date = self.start_date
        one_day = timedelta(days=1)
        ret = []

        while current_date <= self.end_date:
            total = 0
            count = 0
            for row in self.dataset[datatype]:
                this_date = parser.parse(row['date'])
                if (this_date.day == current_date.day
                        and this_date.month == current_date.month):
                    total += row['value']
                    count += 1

            current_date += one_day
            if count:
                ret.append([round(total/count, 2)])
            else:
                ret.append([0.0])
        return ret

    def download_weather_data(self, stations, start_year, num_years):
        nw = noaa_api.NOAAWeatherData(self.noaa_api_token)
        mw = meso_api.MesoWeatherData(self.meso_api_token)

        cur_year = start_year
        num_days = self.end_date - self.start_date
        num_years = num_years

        noaa_stations = [s for s in stations if s['api'] == 'NOAA']
        meso_stations = [s for s in stations if s['api'] == 'MESO']
        print meso_stations

        #TODO: Handle cases where number of days matters...
        while num_years > 0:

            start_date = date(cur_year, self.start_date.month, self.start_date.day)
            end_date = date(cur_year, self.end_date.month, self.end_date.day)

            # data = mw.get_weather_data_from_stations(meso_stations, start_date, end_date)
            # print "Received %d MESOrecords for dates %s - %s" % (len(data), start_date, end_date)
            # self.add_meso_data(data)

            data = nw.get_weather_data_from_stations(noaa_stations, start_date, end_date)
            print "Received %d NOAA records for dates %s - %s" % (len(data), start_date, end_date)
            self.add_noaa_data(data)

            num_years -= 1
            cur_year -= 1

    def dump_raw_data_to_file(self, filename):
        import generated_data
        data = generated_data.weather_data
        with open(filename, "w") as f:
            f.write("weather_data=")
            f.write(str(self.dataset))

    def read_raw_data_from_file(self, filename):
        pass

    def size(self):
        ret = 0
        for k, v in self.dataset.items():
            ret += len(v)
        return ret

