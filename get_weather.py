import config
import my_utils
import weather_dataset
import weather_stations
import sheets
import os

from datetime import datetime
from datetime import timedelta
from dateutil import parser


# INPUT DATA
#============
CALTOPO_INPUT_FILE = "Lassen_June_2020.json"
CALTOPO_STATION_OUTPUT_FILE = "Lassen_June_2020_weather_stations.json"
GOOGLE_SHEET_OUTPUT_FILE="Lassen_June_2020_generated_weather"
OUTPUT_FOLDER="Lassen_June_2020_generated_weather/"

# Only include stations that are within this distance from any given point on trail
# in kilometers
DISTANCE_FROM_TRAIL=50

#Dates are in the format of MM-DD
TRIP_START_DATE="06/19"
TRIP_END_DATE="06/22"

DATA_START_YEAR = 2018
DATA_NUM_YEARS = 10

#============

def main():
    # Parse args
    print ("Reading file \'%s\'"  % (CALTOPO_INPUT_FILE))
    lat_long_list = my_utils.get_lat_long_list_from_file(CALTOPO_INPUT_FILE)

    if not os.path.isdir(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    s = weather_stations.StationGenerator(config.noaa_api_token, config.meso_api_token)

    s.generate_station_list(lat_long_list, min_distance=DISTANCE_FROM_TRAIL)
    print("Retrieved %d stations" % (len(s.station_list)))

    print("Writing station information to \'%s\'" % (OUTPUT_FOLDER + CALTOPO_STATION_OUTPUT_FILE))
    s.write_features_to_file(OUTPUT_FOLDER + CALTOPO_STATION_OUTPUT_FILE)

    stations = s.station_list

    start_date = datetime.strptime(TRIP_START_DATE, "%m/%d")
    end_date = datetime.strptime(TRIP_END_DATE, "%m/%d")
    ds = weather_dataset.WeatherDataset(start_date, end_date, config.noaa_api_token, config.meso_api_token)
    ds.download_weather_data(stations, DATA_START_YEAR, DATA_NUM_YEARS)

    # import generated_data
    # data = generated_data.weather_data
    # ds.add_noaa_data(data)

    ds.dump_raw_data_to_file("generated_data.py")
    # ds.read_raw_data_from_file("generated_data.py")

    print("Writing %d records to \'%s\'" % (ds.size(), GOOGLE_SHEET_OUTPUT_FILE))
    #sheets.write_gsheet(GOOGLE_SHEET_OUTPUT_FILE, ds)

    print("Writing %d records to \'%s\'" % (ds.size(), OUTPUT_FOLDER))
    sheets.write_csvs(OUTPUT_FOLDER, ds)

    return

    # TODO: save CSV?

    if args.meta_data_filename:
        print("Writing meta data to \'%s\'" % (args.meta_data_filename))
        m = generate_meta_data(data)
        write_csv(args.meta_data_filename, m)

if __name__ == "__main__":
    main()
