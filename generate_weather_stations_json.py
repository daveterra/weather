import config
import my_utils
from weather_stations import StationGenerator

import sys
import argparse

def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file',
            help="GEOJson export from caltop or similar source")
    parser.add_argument('-o', '--output-file',
            help="Generates separate GEOJson file specifying nearby NOAA weather stations")
    parser.add_argument('-d', '--distance-from-trail',
            required=False, default=10,
            help="Specify how far from the trail (in km) to look for weather stations")
    args = parser.parse_args()

    print "Reading file \'%s\'"  % (args.input_file)
    lat_long_list = my_utils.get_lat_long_list_from_file(args.input_file)

    s = StationGenerator(config.noaa_api_token)

    s.generate_station_list(lat_long_list, min_distance=args.distance_from_trail)
    print "Retrieved %d stations" % (len(s.station_list))

    print "Writing filtered results to \'%s\'" % (args.output_file)
    s.write_features_to_file(args.output_file)

if __name__ == "__main__":
    main(sys.argv)
