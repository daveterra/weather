
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

