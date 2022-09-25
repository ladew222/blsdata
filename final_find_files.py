import requests
import json
import prettytable
import pandas as pd
import googlemaps
import datetime

df = pd.DataFrame(columns=['location','lat','lon','year','period','period_date','value'])
gmaps_key = googlemaps.Client(key="AIzaSyBlYSDiXeAAKbZQdUEDWCsPhKJPuOA-z7g")

def get_files(fnames):
    headers = {'Content-type': 'application/json'}
    series =  fnames["series_id"].values.tolist()
    data = json.dumps({"seriesid":   series,"startyear":"2014", "endyear":"2018"})
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
    json_data = json.loads(p.text)
    i = 0 
    for series in json_data['Results']['series']:
        location = fnames['area_name'].iloc[i]
        g = gmaps_key.geocode(location)
        lat = g[0]["geometry"]["location"]["lat"]
        lon = g[0]["geometry"]["location"]["lng"]
        i=i+1
        #x=prettytable.PrettyTable(["series id","year","period","value","footnotes"])
        seriesId = series['seriesID']
        print(f"geting:{seriesId}")
        for item in series['data']:
            period = item['period']
            value = item['value']
            if 'M01' <= period <= 'M12':
                month = int(period[1:3])
                period_date = datetime.date(year=item['year'], month=month, day=0)
                df = df.append({'location': location, 'lat': lat, 'lon': lon,'year': item['year'],'period': period,'period_date': period_date, 'value': item['value']},ignore_index=True)


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


def main():
    
    get_file_list()

if __name__ == "__main__":
    main()