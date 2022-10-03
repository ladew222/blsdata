import requests
import json
import pandas as pd
import googlemaps
import datetime
from numpy import random
from math import radians, cos, sin, asin, sqrt

df_inf = []
df_counties = []
gmaps_key = googlemaps.Client(key="AIzaSyBlYSDiXeAAKbZQdUEDWCsPhKJPuOA-z7g")

def dist(lat1, long1, lat2, long2):
    """
Replicating the same formula as mentioned in Wiki
    """
    # convert decimal degrees to radians 
    
    lat1, long1, lat2, long2 = map(radians, [float(lat1), float(long1), float(lat2), float(long2)])
    # haversine formula 
    dlon = long2 - long1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km

def ComputeVals(row):
    return row['Ordinal_7pt'] + row['Ordinal_5pt']


def find_nearest(in_row):
    df= pd.read_csv("out_geo.csv")
    distances = df.apply(
        lambda row: dist(in_row['lat'], in_row['lon'], row['lat'], row['lon']), 
        axis=1)
    return df.loc[distances.idxmin(), 'location']


#can only do 24 series at a time
def get_files(fnames):
    df = pd.DataFrame(columns=['location','coords','lat','lon','year','period','period_date','value'])
    #take individual areas and put into one file via the api and list provided
    headers = {'Content-type': 'application/json'}
    series =  fnames["series_id"].values.tolist()
    data = json.dumps({"seriesid":   series,"startyear":"2013", "endyear":"2019"})
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
    json_data = json.loads(p.text)
    print(f"{json_data['status']}: {json_data['message']} \n")
    i = 0 
    ## each series will have historical data for one area
    for series in json_data['Results']['series']:
        location = fnames['area_name'].iloc[i]
        i=i+1;
        g = gmaps_key.geocode(location)
        ##location found
        if (len(g)>0):
            lat = g[0]["geometry"]["location"]["lat"]
            lon = g[0]["geometry"]["location"]["lng"]
            seriesId = series['seriesID']
            print(f"Processing historical data in:{seriesId} for location :{location}\n")
            for item in series['data']:
                period = item['period']
                value = item['value']
                ##find the month data and instert it into row for place with lat and lon
                if 'M01' <= period <= 'M12':
                    month = int(period[1:3])
                    period_date = datetime.date(year=int(item['year']), month=month, day=int(1))
                    df = df.append({'location': location, 'coords':{'lat': lat, 'lon': lon},'lat': lat, 'lon': lon,'year': item['year'],'period': period,'period_date': period_date, 'value': item['value']},ignore_index=True)

    return(df)

#can only do 24 series at a time
#for sub cpi
def get_sub_areas(subject):
    df = pd.DataFrame(columns=['location','coords','lat','lon','year','period','period_date','value'])
    #take individual areas and put into one file via the api and list provided
    headers = {'Content-type': 'application/json'}
    df_area_names = pd.read_csv('./data/cu_area_names.csv')
    df_area_names = df_area_names.iloc[15: , :]
    df_area_names['series']='CUUR'+ df_area_names['area_code'] + subject
    cnt = df_area_names.shape[0]
    num_loops = int(cnt/15)
    extra=  cnt%15
    x=0
    for x in range(num_loops+1):
        top = x +15
        if x == num_loops:
            series =  df_area_names['series'].iloc[x:x+extra].values.tolist()
        else:
            series =  df_area_names['series'].iloc[x:top].values.tolist()
        x=x+15
        data = json.dumps({"seriesid":   series,"startyear":"2013", "endyear":"2019"})
        p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
        json_data = json.loads(p.text)
        print(f"{json_data['status']}: {json_data['message']} \n")
        i = 0 
        ## each series will have historical data for one area
        for series in json_data['Results']['series']:
            location = df_area_names['area_name'].iloc[i]
            i=i+1;
            g = gmaps_key.geocode(location)
            ##location found
            if (len(g)>0):
                lat = g[0]["geometry"]["location"]["lat"]
                lon = g[0]["geometry"]["location"]["lng"]
                seriesId = series['seriesID']
                print(f"Processing historical data in:{seriesId} for location :{location}\n")
                for item in series['data']:
                    period = item['period']
                    value = item['value']
                    ##find the month data and instert it into row for place with lat and lon
                    if 'M01' <= period <= 'M12':
                        month = int(period[1:3])
                        period_date = datetime.date(year=int(item['year']), month=month, day=int(1))
                        df = df.append({'location': location, 'coords':{'lat': lat, 'lon': lon},'lat': lat, 'lon': lon,'year': item['year'],'period': period,'period_date': period_date, 'value': item['value']},ignore_index=True)

    return(df)

def get_file_list(reload):
    if (reload):
        #collect the list of files from here. Will have to loop through and parse individual
        df_area_names = pd.read_csv('./data/cu_area_names.csv')
        df_area_names = df_area_names.iloc[15: , :]
        df_inf = pd.read_csv('./data/all_areas_inf.csv')
        #df_inf = df_inf[['series_id','sid']]
        df_inf["sid"] =  df_inf["series_id"].str.slice(4, 8)
        df_inf.to_csv('out.csv')  
        #df_inf[df_inf['sid'] >= 'A210']
        #merge area names with list of series which contain the filenames with the data needed
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
        ## we have 2 series numbers for each location where inflation is tracked
        df = get_files(out[['series_id','area_name']].iloc[:24])
        df2 = get_files(out[['series_id','area_name']].iloc[25:49])
        df3 = get_files(out[['series_id','area_name']].iloc[49:74])
        df4 = get_files(out[['series_id','area_name']].iloc[74:])
        all = pd.concat([df, df2], axis=0)
        all = pd.concat([all, df3], axis=0)
        all = pd.concat([all, df4], axis=0)
        return all
    else:
        out = pd.read_csv("out.csv")
        df = get_files(out[['series_id','area_name']].iloc[:24])
        df2 = get_files(out[['series_id','area_name']].iloc[25:49])
        df3 = get_files(out[['series_id','area_name']].iloc[49:74])
        df4 = get_files(out[['series_id','area_name']].iloc[74:])
        all = pd.concat([df, df2], axis=0)
        all = pd.concat([all, df3], axis=0)
        all = pd.concat([all, df4], axis=0)
        return all
        ##now we have a list of areas and series numbers to send to api
   

def get_nearest(df_counties):
    df_counties['name'] = df_counties.apply(
    lambda row: find_nearest(row['lat'], row['lon']), 
    axis=1)


def get_county_data():
    df_counties1 = pd.read_csv("./data/gdp_early.csv",error_bad_lines=False, dtype=str)
    df_counties2 = pd.read_csv("./data/gdp_late.csv",error_bad_lines=False, dtype=str)
    df_counties =  df_counties1.merge(df_counties2, how='left', left_on='GeoFips',right_on='GeoFips')
    df_counties['state'] = df_counties['GeoFips'].str.slice(0,2).astype(int)
    df_counties['county'] = df_counties['GeoFips'].str.slice(2,5).astype(int)
    acs_2019 = pd.read_csv("./data/nhgis0061_csv/nhgis0061_ds245_20195_county_2015-19.csv", encoding = "ISO-8859-1")
    acs_2019b = pd.read_csv("./data/nhgis0061_csv/nhgis0061_ds244_20195_county_2015-19.csv", encoding = "ISO-8859-1")
    acs_2019_all = acs_2019.merge(acs_2019b, how='left', left_on='GISJOIN',right_on='GISJOIN')
    df_counties.columns
    df_county_all = df_counties.merge(acs_2019_all, how='inner', left_on=['state', 'county'], right_on=['STATEA_x', 'COUNTYA_x'])
    df_county_all = df_county_all.dropna(thresh=len(df_county_all) - 10, axis=1)
    ##zillow
    
    df_zillow = pd.read_csv("./data/Metro_median_sale_price_uc_sfrcondo_month.csv")
    df_zillow_cross = pd.read_csv("./data/CountyCrossWalk_Zillow.csv",encoding = "ISO-8859-1")
    df_zillow_all = df_zillow_cross.merge(df_zillow, how='left', left_on='MetroRegionID_Zillow',right_on='RegionID')
    df_county_all2 = df_county_all.merge(df_zillow_all , how='inner', left_on=['STATEA_x', 'COUNTYA_x'], right_on=['StateFIPS', 'CountyFIPS'])
    ##get zip data
    df_zip = pd.read_csv("./data/us_county_latlng.csv", dtype=str)
    df_county_all3 = df_county_all2.merge(df_zip, how='left', left_on='GeoFips',right_on='fips_code')
    ##now get the nearest location for inflation 
    ##geocode the counties
    #df_county_all3['gcode'] = df_county_all3.GeoName_x.apply(gmaps_key.geocode)
    #df_county_all3['lat'] = [g.latitude for g in df_county_all3.gcode]
    #df_county_all3['lon'] = [g.longitude for g in df_county_all3.gcode]

    df_county_all3['inf_city'] = df_county_all3.apply(find_nearest, axis=1)
    df_county_all3
    df_county_all3.to_csv('all_counties.csv') 



def assign_sub_inflation():   
    global df_inf
    global df_counties
    df_inf = pd.read_csv("out_geo2.csv")
    df_counties= pd.read_csv("all_counties.csv")
    for i, row in df_counties.iterrows():
        for index, row2 in df_inf.iterrows():
            if row2['location'] == row['inf_city']:
                month = row2['period'][1:]
                period_date = datetime.date(year=int(row2['year']), month=int(month), day=int(2))
                date_time = period_date.strftime("%m/%d/%Y")
                df_counties.at[i,date_time] = row2['value']
    df_counties.to_csv('all_counties_a.csv') 
             
    
def assign_inflation():   
    global df_inf
    global df_counties
    df_inf = pd.read_csv("out_geo.csv")
    df_counties= pd.read_csv("all_counties_a.csv")
    for i, row in df_counties.iterrows():
        for index, row2 in df_inf.iterrows():
            if row2['location'] == row['inf_city']:
                month = row2['period'][1:]
                period_date = datetime.date(year=int(row2['year']), month=int(month), day=int(1))
                date_time = period_date.strftime("%m/%d/%Y")
                df_counties.at[i,date_time] = row2['value']

    df_counties.to_csv('out_fin.csv') 
    
def main():
    ########
    # Get County Data includes Zillow,BEA, and Census
    # This pulls the data. It will then merge the data by state id and county
    # In some data this comes as one string.  We need to break apart and create fields
    # then we can join togehter on common keys.
    # The bea data is monthly like Zillow but their is missing data for locations where county GPD not tracked
    # outputs all_counties.csv
    #######
    GetCounty = False # get all_counties.csv
    if GetCounty ==True:
        get_county_data()
        
    #####
    # This will pull a new list of bls location file names and geocode their latatutide and longitude
    # ** this step is neccessary because the bls has their data availble by location not by agregate
    # with the neccessary detail.
    # It then uses the list of file names and send to BLS via the API which will allow us to extract
    # the monthly longitual CPI for each county
    # We then put the longitual data in a row of out_geo.csv which will match to a location
    # Returns out_geo.csv
    #####
    GetGeoCoded = False  #get out_geo.csv
    if (GetGeoCoded):
         ### True to get new list of locations
         df=get_file_list(True)
         ##false if already processed report file listings
         df.to_csv('out_geo.csv') 
    else:
        df= pd.read_csv("out_geo.csv")
    
    GetGeoCoded2 = False  #get out_geo2.csv
    if (GetGeoCoded2):
         ### True to get new list of locations
         df=get_sub_areas('SAH')
         ##false if already processed report file listings
         df.to_csv('out_geo2.csv') 
    else:
        df= pd.read_csv("out_geo2.csv")
    #######
    # This will take our merged county data and find the closest cpi data in a row of 
    # out_geo.csv
    # It will then assign all appropriate longiutal data from out_geo for the match
    # the rows should then have date fields with */*/* dates for inflation where available
    # the final output should be out_fin.csv.
    # Like the the bea data there are gaps in this data where the BLS did not have data for
    # a location and time period.
    ####### 
    assign_sub_inflation()
    #assign_inflation()  #merge out_geo and and all_counties using geograhic correlation
        
   
    #save data for later use
        

if __name__ == "__main__":
    main()