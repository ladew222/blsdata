import requests
import json
import prettytable
import pandas as pd


def get_files(fnames):
    headers = {'Content-type': 'application/json'}
    series = fnames.to_json
    data = json.dumps({"seriesid": fnames.values.tolist(),"startyear":"2018", "endyear":"2021"})
    p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
    json_data = json.loads(p.text)
    for series in json_data['Results']['series']:
        x=prettytable.PrettyTable(["series id","year","period","value","footnotes"])
        seriesId = series['seriesID']
        print(f"geeting:{seriesId}")
        for item in series['data']:
            year = item['year']
            period = item['period']
            value = item['value']
            footnotes=""
            for footnote in item['footnotes']:
                if footnote:
                    footnotes = footnotes + footnote['text'] + ','
            if 'M01' <= period <= 'M12':
                x.add_row([seriesId,year,period,value,footnotes[0:-1]])
    #output = open("full" + '.txt','a')
    #output.write (x.get_string())
    #output.close()
    print(x.get_string())

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
    out = out[out['rep_type'] == 'S']
    out.to_csv('out.csv')
    get_files(out['series_id'].head())


def main():
    get_file_list()

if __name__ == "__main__":
    main()