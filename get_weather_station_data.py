import noaa_api
import my_utils
import config

import csv
import json
# using geojson 2.4.1
import geojson
import argparse

import pygsheets
from pygsheets.custom_types import ChartType
import numpy

from datetime import datetime
from datetime import timedelta
from dateutil import parser

class WeatherData:
    def __init__(self, noaa_api_token, dataset='GHCND'):
        self.noaa_api = noaa_api.NOAA(noaa_api_token)
        self.dataset=dataset

    def _get_station_elevations(self, which_station, stations):
        ret = { 'elevation' : 0, 'elevationUnit' : ''}
        for s in stations:
            if s['id'] == which_station:
                ret['elevation'] = s['elevation']
                ret['elevationUnit'] = s['elevationUnit']
                break

        return ret

    def get_weather_data_from_stations(self, stations, start_date, end_date, datatypes):
        data = []

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
                    datatypeid=datatypes,
                    stationid=station_ids,
                    startdate=start_date,
                    enddate=end_date,
                    sortfield='date',
                    sortorder='desc',
                    limit=limit,
                    offset=offset)
            if d is None:
                print "\tRequest failed, retrying"
                continue

            if len(d) <= 0:
                break
            for i in d:
                i.update(self._get_station_elevations(i['station'], stations))
                records_appended += 1
                data.append(i)
            offset += len(d)
        return data

def loop_over_dates(args, stations, data_filter):
    w = WeatherData(config.noaa_api_token)
    cur_year = args.start_year
    num_days = args.end_date - args.start_date
    num_years = args.num_years
    weather_data = []

    #TODO: Handle cases where number of days matters...
    while num_years > 0:
        start_date = "%s-%02d-%02d" % (cur_year, args.start_date.month, args.start_date.day)
        end_date = "%s-%02d-%02d" % (cur_year, args.end_date.month, args.end_date.day)

        data = w.get_weather_data_from_stations(stations, start_date, end_date, data_filter)
        print "Received %d records for dates %s - %s" % (len(data), start_date, end_date)

        weather_data.extend(data)
        num_years -= 1
        cur_year -= 1

    return weather_data

def generate_meta_data(data):
    meta_data = []

    # Generate list of datatypes
    datatypes=[]
    for d in data:
        dt = d['datatype']
        if dt not in datatypes:
            datatypes.append(dt)

    for datatype in datatypes:
        l = []
        for d in data:
            if d['datatype'] == datatype:
                l.append(d['value'])

        temp = {'datatype': datatype,
                'min': min(l),
                'max': max(l),
                'avg': round(sum(l)/len(l),2),
                'count': len(l)}
        meta_data.append(temp)

    return meta_data


def valid_date(s):
    try:
        return datetime.strptime(s, "%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def write_csv(filename, to_csv):
    with open(filename, 'w') as out:
        keys = to_csv[0].keys()
        dict_writer = csv.DictWriter(out, keys)
        dict_writer.writeheader()
        dict_writer.writerows(to_csv)

class WeatherDataset():
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

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
            ret.append([round(total/count, 2)])
        return ret

    def size(self):
        ret = 0
        for k, v in self.dataset.items():
            ret += len(v)
        return ret


def write_gsheet(filename, ds):

    matrix = {}
    keys = ds.get_data_keys()

    gc = pygsheets.authorize()

    try:
        sh = gc.open(filename)
        sh.delete()
    except:
        pass

    sh = gc.create(filename)

    index=0

    for datatype in ds.get_data_types():

        wks = sh.add_worksheet(datatype, index=index)
        index += 1

        data = ds.get_matrix_for_datatype(datatype)
        wks.update_values('A1', data)

        lastB = 'B' + str(len(data) - 1)
        lastA = 'A' + str(len(data) - 1)
        domain = ('A1', lastA)
        chart_type = ChartType('LINE')
        r = [('B2', lastB)]

        chart = wks.add_chart(domain, r, datatype, anchor_cell='A1', chart_type=chart_type)

    # Add metadata
    wks = sh.add_worksheet("Averages", index=0)
    date_values = ds.get_date_keys()
    num_dates   = len(date_values) + 1
    dates_range = 'A2:A' + str(num_dates)
    wks.update_values(dates_range, date_values)

    i = 1
    temp_ranges = []
    water_ranges = []
    for datatype in ds.get_data_types():
        col = str(chr(ord('A')+i))
        data_range = "%s%d:%s%d" % (col, 2, col, 2+num_dates)

        # Add for chart later
        data_range_tuple = ("%s%d" % (col, 1), "%s%d" % (col, 1+num_dates))
        if 'temp' in datatype:
            temp_ranges.append(data_range_tuple)
        else:
            water_ranges.append(data_range_tuple)

        wks.update_row(1, [[datatype]], col_offset=i)
        d = ds.get_matrix_for_datatype_averaged(datatype)
        wks.update_values( data_range, d )
        i += 1

    anchor = str(chr(ord('A')+i)) + "1"
    chart_type = ChartType('LINE')
    domain = ('A1', 'A' + str(num_dates))
    chart = wks.add_chart(domain, temp_ranges, "averages",
            anchor_cell=anchor, chart_type=chart_type)

    anchor = str(chr(ord('A')+i)) + "20"
    chart_type = ChartType('LINE')
    domain = ('A1', 'A' + str(num_dates))
    chart = wks.add_chart(domain, water_ranges, "averages", 
            anchor_cell=anchor, chart_type=chart_type)


    print sh.url
    sh.share('', role='reader', type='anyone')
    return

def main():
    # Parse args
    default_start_year = datetime.now().year - 1
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file',
            help="GEOJson containing weather station data. Use `generate_weather_station_json.py` first")
    parser.add_argument('-o', '--output-file',
            help="Generates csv file containing weather data from provided stations")
    parser.add_argument("-s", "--start-date",
            required=True, type=valid_date,
            help="The  - format MM-DD")
    parser.add_argument("-e", "--end-date",
            required=True, type=valid_date,
            help="The  - format MM-DD")
    parser.add_argument("-n", "--num-years",
            required=False, default=1, type=int,
            help="The number of years to include in results")
    parser.add_argument("-y", "--start-year",
            required=False, default=default_start_year, type=int,
            help="The number of years to include in results")
    parser.add_argument("-m", "--meta-data-filename",
            required=False,
            help="Generate metadata as part of CSV output (min, max, avg for each datatype)")

    args = parser.parse_args()

    stations = my_utils.get_station_list_from_file(args.input_file)
    print "Read %d stations from \'%s\'" % (len(stations), args.input_file)

    ds = WeatherDataset(args.start_date, args.end_date)
    data_filter = ds.get_noaa_data_filter()

    # Loop over dates...
    data = loop_over_dates(args, stations, data_filter)

    # import generated_data
    # data = generated_data.weather_data
    with open("generated_data.py", "w") as f:
        f.write("weather_data=")
        f.write(str(data))

    ds.add_noaa_data(data)

    print "Writing %d records to \'%s\'" % (ds.size(), args.output_file)
    write_gsheet(args.output_file, ds)
    return

    print "Writing %d records to \'%s\'" % (len(data), args.output_file)
    write_csv(args.output_file, data)

    if args.meta_data_filename:
        print "Writing meta data to \'%s\'" % (args.meta_data_filename)
        m = generate_meta_data(data)
        write_csv(args.meta_data_filename, m)

main()

