
import requests

class noaa_api:
    def __init__(self, token):
        self.base_url = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/'
        self.token = {'token': token}

    def call_api(self, request, params):
        s = requests.Session()
        url = self.base_url + request
        p = requests.Request('GET', url, headers=self.token, params=params).prepare()
        r = s.send(p)

        if not r.ok:
            print("Error: " + str(r.status_code))
            print r.content
            return None
        else:
            r = r.json()
            if 'results' not in r: 
                return r
            return r['results']

    def get_datasets(self, **kwargs):
        req_type = 'datasets'
        return self.call_api(req_type, kwargs)

    def get_datasets_with_id(self, which_id, **kwargs):
        req_type = 'datasets/' + which_id
        return self.call_api(req_type, kwargs)

    def get_data_categories(self, **kwargs):
        req_type = 'datacategories'
        return self.call_api(req_type, kwargs)

    def get_data_categories_with_id(self, which_id, **kwargs):
        req_type = 'datacategories/' + which_id
        return self.call_api(req_type, kwargs)

    def get_data_types(self, **kwargs):
        req_type = 'datatypes'
        return self.call_api(req_type, kwargs)

    def get_data_types_by_id(self, which_id, **kwargs):
        req_type = 'datatypes/' + which_id
        return self.call_api(req_type, kwargs)

    def get_location_categories(self, **kwargs):
        req_type = 'locationcategories'
        return self.call_api(req_type, kwargs)

    def get_location_categories_with_id(self, which_id, **kwargs):
        req_type = 'locationcategories/' + which_id
        return self.call_api(req_type, kwargs)

    def get_locations(self, **kwargs):
        req_type = 'locations'
        return self.call_api(req_type, kwargs)

    def get_locations_with_id(self, which_id, **kwargs):
        req_type = 'locations/' + which_id
        return self.call_api(req_type, kwargs)

    def get_stations(self, **kwargs):
        req_type = 'stations'
        return self.call_api(req_type, kwargs)

    def get_stations_with_id(self, which_id, **kwargs):
        req_type = 'stations/' + which_id
        return self.call_api(req_type, kwargs)

    def get_data(self, dataset_id, **kwargs):
        req_type = 'data?datasetid=' + dataset_id
        return self.call_api(req_type, kwargs)


