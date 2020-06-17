import csv
import os
import pygsheets
from pygsheets.custom_types import ChartType

def write_gsheet(filename, ds):

    matrix = {}
    keys = ds.get_data_keys()

    gc = pygsheets.authorize(client_secret='/Users/dave/code/weather/client_secret.json')

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
        if not data:
            continue

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


    print(sh.url)
    sh.share('', role='reader', type='anyone')
    return

def write_csvs(foldername, ds):
    matrix = {}
    keys = ds.get_data_keys()

    index=0
    if not os.path.isdir(foldername):
        os.makedirs(foldername)

    for datatype in ds.get_data_types():
        filename=foldername + datatype + ".csv"
        keys = ds.get_data_keys()
        print(filename)
        with open(filename, 'w', newline='') as out:
            data = ds.get_matrix_for_datatype(datatype)
            writer = csv.writer(out)
            writer.writerow(keys)
            if not data:
                continue
            writer.writerows(data)

    filename = foldername + "averages.csv"
    with open(filename, 'w', newline='') as out: 
        data = ds.get_matrix_for_datatype_averaged(datatype)
        writer = csv.writer(out)
        writer.writerows(data)



    # Add metadata
    # file = foldername/averages
    # wks = sh.add_worksheet("Averages", index=0)
    # date_values = ds.get_date_keys()
    # num_dates   = len(date_values) + 1
    # dates_range = 'A2:A' + str(num_dates)
    # wks.update_values(dates_range, date_values)

    return

def write_csv(filename, to_csv):
    with open(filename, 'w') as out:
        keys = to_csv[0].keys()
        dict_writer = csv.DictWriter(out, keys)
        dict_writer.writeheader()
        dict_writer.writerows(to_csv)

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

