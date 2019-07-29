import noaa_api
import my_utils
import config
import sheets
import weather_dataset

import json
# using geojson 2.4.1
import geojson
import argparse

from datetime import datetime
from dateutil import parser

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

    ds = weather_dataset.WeatherDataset(args.start_date, args.end_date, config.noaa_api_token, config.meso_api_token)
    ds.download_weather_data(stations, args.start_year, args.num_years)

    print "Writing %d records to \'%s\'" % (ds.size(), args.output_file)
    sheets.write_gsheet(args.output_file, ds)
    return

    print "Writing %d records to \'%s\'" % (len(data), args.output_file)
    write_csv(args.output_file, data)

    if args.meta_data_filename:
        print "Writing meta data to \'%s\'" % (args.meta_data_filename)
        m = generate_meta_data(data)
        write_csv(args.meta_data_filename, m)

main()

