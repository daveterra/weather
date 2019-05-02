from noaa_api_v2 import NOAAData
import csv
import json
import ast
# using geojson 2.4.1
import geojson

from datetime import datetime
from dateutil import parser

input_file = "JMT_weather.json"
output_file = "JMT_weather.csv"
input_file = "Hat_Creek_Rim_weather.json"
output_file = "Hat_Creek_Rim_weather.csv"
api_token = ""
noaa_api = NOAAData(api_token)

min_mon = 9
min_day = 27
max_mon = 10
max_day = 14
furthest_year = 2008
current_year = 2019
dataset = 'GSOM'

def get_station_elevations(which_station, stations):
    ret = { 'elevation' : 0, 'elevationUnit' : ''}
    for s in stations:
        if s['id'] == which_station:
            ret['elevation'] = s['elevation']
            ret['elevationUnit'] = s['elevationUnit']
            break

    return ret

def get_weather_data_from_stations(stations): #, start_date, end_date):
    data = []
    dataset = 'GHCND'

    num_stations = len(stations)
    cur_station_num = 1

    station_ids = []
    # Build station list
    for station in stations:
        station_ids.append(station['id'])
    cur_year = current_year

    while cur_year > furthest_year:
        start_date = "%s-%02d-%02d" % (cur_year, min_mon, min_day)
        end_date = "%s-%02d-%02d" % (cur_year, max_mon, max_day)

        limit = 10
        offset = 0
        records_appended = 0
        while True:
            d = noaa_api.fetch_data(
                    dataset_id=dataset,
                    units='standard',
                    datatypeid='TMIN',
                    stationid=station_ids,
                    startdate=start_date,
                    enddate=end_date,
                    sortfield='date',
                    sortorder='desc',
                    limit=limit,
                    offset=offset)

            print d
            if d is None:
                print "\tRequest failed, retrying"
                continue

            if len(d) <= 0:
                break
            for i in d:
                i.update(get_station_elevations(i['station'], stations))
                records_appended += 1
                data.append(i)
            offset += len(d)
        print "\treceived %d records for year %d" % (records_appended, cur_year)

        cur_year -= 1
        if cur_year < furthest_year:
            break

    return data

def get_station_list_from_file(file_name):
    final_list = []
    with open(file_name) as json_file:
        weather_folder_id = ''
        feature_collection = geojson.load(json_file)

        #get folder id for 'weather' folder
        for f in feature_collection['features']:
            p = f['properties']
            if p['class'] == 'Folder' and p['title'] == 'weather':
                weather_folder_id = f['id']
                break
        if weather_folder_id == '':
            return

        for f in feature_collection['features']:
            p = f['properties']
            if p['class'] == 'Marker' and p['folderId'] == weather_folder_id:
                d = ast.literal_eval(p['description'])
                final_list.append(d)
        return final_list

def main():

    stations = get_station_list_from_file(input_file)
    print "Read %d stations from \'%s\'" % (len(stations), input_file)

    # import generated_data
    # data = generated_data.weather_data

    data = get_weather_data_from_stations(stations)

    with open("generated_data.py", "w") as f:
        f.write("weather_data=")
        f.write(str(data))

    data = filter(lambda d: d['datatype'] in ('TMAX', 'TMIN'), data)

    # data.sort(key=lambda d: d['date'], reverse=True)
    # for d in data:
    #     print d
    # print len(data)

    to_csv = data
    keys = to_csv[0].keys()
    print "Writing %d records to \'%s\'" % (len(to_csv), output_file)
    with open(output_file, 'w') as out:
        dict_writer = csv.DictWriter(out, keys)
        dict_writer.writeheader()
        dict_writer.writerows(to_csv)


main()
