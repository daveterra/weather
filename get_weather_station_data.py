import noaa_api
import my_utils
import config

import csv
import json
# using geojson 2.4.1
import geojson
import argparse

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

    def get_weather_data_from_stations(self, stations, start_date, end_date):
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
                    # datatypeid='TMIN', # TODO: Make this an input or a config
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

        data = w.get_weather_data_from_stations(stations, start_date, end_date)
        print "Received %d records for dates %s - %s" % (len(data), start_date, end_date)

        weather_data.extend(data)
        num_years -= 1
        cur_year -= 1

    return weather_data


def valid_date(s):
    try:
        return datetime.strptime(s, "%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

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
            required=False, default=10, type=int,
            help="The number of years to include in results")
    parser.add_argument("-y", "--start-year",
            required=False, default=default_start_year, type=int,
            help="The number of years to include in results")

    args = parser.parse_args()

    stations = my_utils.get_station_list_from_file(args.input_file)
    print "Read %d stations from \'%s\'" % (len(stations), args.input_file)

    # Loop over dates...
    data = loop_over_dates(args, stations)

    # import generated_data
    # data = generated_data.weather_data

    with open("generated_data.py", "w") as f:
        f.write("weather_data=")
        f.write(str(data))

    data = filter(lambda d: d['datatype'] in ('TMAX', 'TMIN'), data)

    to_csv = data
    keys = to_csv[0].keys()
    print "Writing %d records to \'%s\'" % (len(to_csv), args.output_file)
    with open(args.output_file, 'w') as out:
        dict_writer = csv.DictWriter(out, keys)
        dict_writer.writeheader()
        dict_writer.writerows(to_csv)


main()

