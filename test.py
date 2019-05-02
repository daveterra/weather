import noaa_api
import json
import config

noaa = noaa_api.NOAA(config.noaa_api_token)

def get_datasets():
    datasets = []
    count = 0
    step = 10
    dataset='GHCND'
    while True:
        temp = noaa.get_datasets(sortfield='name', offset=count, limit=step)
        # temp = data.datasets_with_id(which_id=dataset, sortfield='name', offset=count, limit=step)
        count += len(temp)
        datasets.extend(temp)
        if len(temp) < step:
            break

    print "DATA SETS"
    for i in datasets:
        print(i)

def get_data_categories():
    data_categories = []
    count = 0
    step = 10
    while True:
        temp = noaa.get_data_categories(sortfield='name', offset=count, limit=step)
        count += len(temp)
        data_categories.extend(temp)
        if len(temp) < step:
            break
    print "DATA CATAGORIES"
    for i in data_categories:
        print(i)

def get_data_types():
    dataset='GHCND'
    # data_types = noaa.get_data_types_by_id('TMIN', sortfield='name', datasetid=dataset, stationid='GHCND:USC00045280')
    data_types = noaa.get_data_types(sortfield='name', datasetid=dataset, stationid='GHCND:USC00045280')
    print "DATA TYPES"
    for i in data_types:
        print(i)


get_datasets()
# get_data_types()
# get_data_categories()

# location_categories = noaa.get_location_categories(sortfield='name')
# print "LOCATION CATAGORIES"
# for i in location_categories:
#     print(i)


# zips = noaa.get_locations(locationcatagoryid='ZIP', sortfield='name', sortorder='asc')
# print "ZIPS"
# for i in zips:
#     print(i)


