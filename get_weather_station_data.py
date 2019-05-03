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

def loop_over_dates(args, stations):
    w = WeatherData(config.noaa_api_token)
    cur_year = args.start_year
    num_days = args.end_date - args.start_date
    num_years = args.num_years
    weather_data = []

    #TODO: Handle cases where number of days matters...
    while num_years > 0:
        start_date = "%s-%02d-%02d" % (cur_year, args.start_date.month, args.start_date.day)
        end_date = "%s-%02d-%02d" % (cur_year, args.end_date.month, args.end_date.day)

        data = w.get_weather_data_from_stations(stations, start_date, end_date, args.data_types)
        print "Received %d records for dates %s - %s" % (len(data), start_date, end_date)

        weather_data.extend(data)
        num_years -= 1
        cur_year -= 1

    return weather_data

def generate_meta_data(data):
    #TODO: Generate metadata per station?
    #data = filter(lambda d: d['datatype'] in ('TMAX', 'TMIN'), data)
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

def write_gsheet(filename, data):
    matrix = {}
    keys = ['date', 'value', 'station', 'elevation']

    for i in data:
        datatype = i['datatype']
        if datatype not in matrix:
            matrix[datatype] = [keys]
        row = [i[k] for k in keys]
        matrix[datatype].append(row)


    gc = pygsheets.authorize()

    try:
        sh = gc.open(filename)
        sh.delete()
    except:
        pass

    sh = gc.create(filename)

    index=0
    for datatype, data in matrix.items():

        wks = sh.add_worksheet(datatype, index=index)
        index += 1

        wks.update_values('A1', data)

        lastB = 'B' + str(len(data) - 1)
        lastA = 'A' + str(len(data) - 1)
        domain = ('A1', lastA)
        chart_type = ChartType('LINE')
        r = [('B2', lastB)]

        print domain
        print r
        chart = wks.add_chart(domain, r, 'test', anchor_cell='A1', chart_type=chart_type)
        print chart.get_json()

    print sh.url
    sh.share('', role='reader', type='anyone')
    return

    # Open spreadsheet and then workseet
    wks = sh.sheet1
    wks.update_values('A1', matrix)

    # matrix = numpy.array(data[0].keys())
    # matrix = numpy.array()
    # wks.append_table())

    # Update a cell with value (just to let him know values is updated ;) )
    wks.update_value('A1', "Hey yank this numpy array")
    my_nparray = np.random.randint(10, size=(3, 4))

    # update the sheet with array
    wks.update_values('A2', my_nparray.tolist())


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
    parser.add_argument("-d", "--data-types",
            nargs="+", required=False,
            help="Space separated list of NOAA datatypes to filter on, if left blank will grab all available data")
    parser.add_argument("-m", "--meta-data-filename",
            required=False,
            help="Generate metadata as part of CSV output (min, max, avg for each datatype)")

    args = parser.parse_args()
    print args.data_types

    stations = my_utils.get_station_list_from_file(args.input_file)
    print "Read %d stations from \'%s\'" % (len(stations), args.input_file)

    # Loop over dates...
    # data = loop_over_dates(args, stations)

    import generated_data
    data = generated_data.weather_data
    with open("generated_data.py", "w") as f:
        f.write("weather_data=")
        f.write(str(data))

    print "Writing %d records to \'%s\'" % (len(data), args.output_file)
    write_gsheet(args.output_file, data, args.start_date, args.end_date, args.num_years)
    return

    print "Writing %d records to \'%s\'" % (len(data), args.output_file)
    write_csv(args.output_file, data)

    if args.meta_data_filename:
        print "Writing meta data to \'%s\'" % (args.meta_data_filename)
        m = generate_meta_data(data)
        write_csv(args.meta_data_filename, m)

main()

