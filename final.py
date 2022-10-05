import requests
import json
import pandas as pd
import googlemaps
import datetime
from numpy import random
from math import radians, cos, sin, asin, sqrt

df_inf = []
df_counties = []
df_area_names =[]
gmaps = googlemaps.Client(key="AIzaSyBlYSDiXeAAKbZQdUEDWCsPhKJPuOA-z7g")

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
    df = pd.read_csv("./output/bls_areas.csv")
    distances = df.apply(
        lambda row: dist(in_row['lat'], in_row['lon'], row['lat'], row['lon']), 
        axis=1)
    return df.loc[distances.idxmin(), 'area_name']


#can only do 24 series at a time
## see https://www.bls.gov/developers/api_faqs.htm
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
        g = gmaps.geocode(location)
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

    df = pd.DataFrame(columns=['location','series','coords','lat','lon','year','period','period_date','value'])
    #take individual areas and put into one file via the api and list provided
    headers = {'Content-type': 'application/json'}
    df_area_names = pd.read_csv('./output/bls_areas.csv')
    #remove non local
    df_area_names = df_area_names.iloc[15: , :]
    df_area_names['series']='CUUR'+ df_area_names['area_code'] + subject
    cnt = df_area_names.shape[0]
    ## 15 at a time to keep the api happy
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
        reg_key = 'fc673660b7364f53ba5f9a530c89a82e'
        data = json.dumps({"seriesid":   series,"startyear":"2013", "endyear":"2019","registrationkey":reg_key})
        p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
        json_data = json.loads(p.text)
        print(f"{json_data['status']}: {json_data['message']} \n")
        i = 0 
        ## each series will have historical data for one area
        for series in json_data['Results']['series']:
            location = df_area_names['area_name'].iloc[i]
            lat = df_area_names['lat'].iloc[i]
            lon = df_area_names['lon'].iloc[i]
            i=i+1;
            g = gmaps.geocode(location)
            ##location found
            seriesId = series['seriesID']
            print(f"Processing historical data in:{seriesId} for location :{location}\n")
            for item in series['data']:
                period = item['period']
                value = item['value']
                ##find the month data and instert it into row for place with lat and lon
                if 'M01' <= period <= 'M12':
                    month = int(period[1:3])
                    period_date = datetime.date(year=int(item['year']), month=month, day=int(1))
                    df = df.append({'location': location, 'series':subject , 'coords':{'lat': lat, 'lon': lon},'lat': lat, 'lon': lon,'year': item['year'],'period': period,'period_date': period_date, 'value': item['value']},ignore_index=True)

    return(df)




def get_nearest(df_counties):
    df_counties['name'] = df_counties.apply(
    lambda row: find_nearest(row['lat'], row['lon']), 
    axis=1)


def get_county_data():
    global df_counties
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
    ## and geocode the counties
    df_county_all3['inf_city'] = df_county_all3.apply(find_nearest, axis=1)
    df_counties = df_county_all3
    df_county_all3.to_csv('./output/all_counties.csv') 
    return df_county_all3



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
    return df_counties
             
def geocode_bls_areas():
    df_area_names = pd.read_csv('./data/cu_area_names.csv')
    #remove non local
    df_area_names = df_area_names.iloc[15: , :]
    df_area_names = df_area_names.reset_index(drop=True)
    df_area_names['lon'] = ""
    df_area_names['lat'] = ""
    max =len(df_area_names)-1
    for x in range(max):
        geocode_result = gmaps.geocode(df_area_names['area_name'].iloc[x])
        try:
            df_area_names.at[x,'lat']=geocode_result[0]['geometry']['location']['lat']
            df_area_names.at[x,'lon']=geocode_result[0]['geometry']['location']['lng']
        except IndexError:
            print("Address was wrong..."+ df_area_names['area_name'])
        except Exception as e:
            print("Unexpected error occurred.", e )
    return  df_area_names

    
      
def assign_inflation(df_in, df_counties):   
    for i, row in df_counties.iterrows():
        for index, row2 in df_in.iterrows():
            if row2['location'] == row['inf_city']:
                month = row2['period'][1:]
                period_date = datetime.date(year=int(row2['year']), month=int(month), day=int(1))
                date_time = row2['series'] + '_' + period_date.strftime("%m/%d/%Y")
                df_counties.at[i,date_time] = row2['value']
    
    df_counties.to_csv('out_fin.csv') 
    return df_counties
    
def main():
        #####
    # We will pull a new list of bls location file names
    # ** this step is neccessary because the bls has their data availble by location not by agregate
    # with the neccessary detail.
    # It then uses the list of file names and send to BLS via the API which will allow us to extract
    # the monthly longitual CPI for each county
    # We then put the longitual data in a row of out_geo.csv which will match to a location
    # Returns cu_area_names.csv which will be used later
    #####
    
    GetBLS = True # get all_counties.csv
    if GetBLS ==True:
        bls_areas = geocode_bls_areas()
        bls_areas.to_csv('./output/bls_areas.csv') 
    else:
        bls_areas = pd.read_csv("./output/bls_ares.csv")

    
    ########
    # Get County Data includes Zillow,BEA, and Census
    # This pulls the data. It will then merge the data by state id and county
    # In some data this comes as one string.  We need to break apart and create fields
    # then we can join togehter on common keys.
    # The bea data is monthly like Zillow but their is missing data for locations where county GPD not tracked
    # outputs all_counties.csv which will be merged
    # It will then look at the location of closest CPI data and assign it to a county 
    ####### 
    GetCounty = True # get all_counties.csv
    if GetCounty ==True:
        df_counties = get_county_data()
    else:
        df_counties = pd.read_csv("./output/all_counties.csv")
        
    #######
    # This will take our merged county data and find the closest cpi data in a row of 
    # out_geo.csv
    # It will then assign all appropriate longiutal data from out_geo for the match
    # the rows should then have date fields with */*/* dates for inflation where available
    # the final output should be out_fin.csv.
    # Like the the bea data there are gaps in this data where the BLS did not have data for
    # a location and time period.
    # outputs df_final.csv
    ####### 
    cpi_df=get_sub_areas('SAH')
    cpi_house=get_sub_areas('SA0')
    df_counties =assign_inflation(cpi_df, df_counties)
    df_counties =assign_inflation(cpi_house, df_counties)
    #merge out_geo and and all_counties using geograhic correlation
    #save data for later use
    df_counties.to_csv('./output/df_final.csv') 
        

if __name__ == "__main__":
    main()