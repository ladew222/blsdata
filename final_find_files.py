import requests
import json
import prettytable
import pandas as pd
import googlemaps
import datetime
from numpy import random
from math import radians, cos, sin, asin, sqrt

df = pd.DataFrame(columns=['location','coords','lat','lon','year','period','period_date','value'])
gmaps_key = googlemaps.Client(key="AIzaSyBlYSDiXeAAKbZQdUEDWCsPhKJPuOA-z7g")

t
def dist(lat1, long1, lat2, long2):
    """
Replicating the same formula as mentioned in Wiki
    """
    # convert decimal degrees to radians 
    lat1, long1, lat2, long2 = map(radians, [lat1, long1, lat2, long2])
    # haversine formula 
    dlon = long2 - long1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km

def find_nearest(lat, long):
    distances = df.apply(
        lambda row: dist(lat, long, row['lat'], row['lon']), 
        axis=1)
    return df.loc[distances.idxmin(), 'location']



def get_files(fnames):
    headers = {'Content-type': 'application/json'}
    series =  fnames["series_id"].values.tolist()
    data = json.dumps({"seriesid":   series,"startyear":"2014", "endyear":"2018"})
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
    json_data = json.loads(p.text)
    print(f"{json_data['status']}: {json_data['message']}")
    i = 0 
    for series in json_data['Results']['series']:
        location = fnames['area_name'].iloc[i]
        g = gmaps_key.geocode(location)
        lat = g[0]["geometry"]["location"]["lat"]
        lon = g[0]["geometry"]["location"]["lng"]
        i=i+1
        #x=prettytable.PrettyTable(["series id","year","period","value","footnotes"])
        seriesId = series['seriesID']
        print(f"Processing:{seriesId}")
        for item in series['data']:
            period = item['period']
            value = item['value']
            if 'M01' <= period <= 'M12':
                month = int(period[1:3])
                period_date = datetime.date(year=item['year'], month=month, day=0)
                df = df.append({'location': location, 'coords':{'lat': lat, 'lon': lon},'lat': lat, 'lon': lon,'year': item['year'],'period': period,'period_date': period_date, 'value': item['value']},ignore_index=True)


def get_file_list():
    df_area_names = pd.read_csv('cu_area_names.csv')
    df_area_names = df_area_names.iloc[15: , :]
    df_inf = pd.read_csv('all_areas_inf.csv')
    #df_inf = df_inf[['series_id','sid']]
    df_inf["sid"] =  df_inf["series_id"].str.slice(4, 8)
    df_inf.to_csv('out.csv')  
    #df_inf[df_inf['sid'] >= 'A210']
    df_merge_left = df_area_names.merge(df_inf, how='left', left_on='area_code',right_on='sid')
    df_merge_left = df_merge_left.drop_duplicates(subset=['series_id','area_name'], keep='first')
    df_merge_left['series_id']= df_merge_left['series_id'].str.strip()
    df_merge_left= df_merge_left[['series_id','area_name']].drop_duplicates(subset = ["series_id"])
    df_merge_left = df_merge_left[['area_name','series_id']]
    df_merge_left.to_csv('out.csv')
    #df_m2 = df_merge_left[df_merge_left['series_id'].str.endswith('0')]
    #df = df_merge_left[df_merge_left['series_id'].str[-3:]=='SA0']
    df_merge_left["rep_id"] =  df_merge_left["series_id"].str.slice(8,11)
    df_merge_left["rep_type"] =  df_merge_left["series_id"].str.slice(3,4)
    out = df_merge_left[df_merge_left['rep_id'].str.contains("SA0")]
    #out = out[out['rep_type'] == 'R']
    out.to_csv('out.csv')
    get_files(out[['series_id','area_name']].head())

def get_nearest(df_counties):
    df_counties['name'] = df_counties.apply(
    lambda row: find_nearest(row['lat'], row['lon']), 
    axis=1)

def main():
    
    get_file_list()

if __name__ == "__main__":
    main()