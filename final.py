import requests
import json
import prettytable

##APU020072610 gas 	APU010072610
###'CUUR0000SA0L1E','SUUR0000SAH2','SUUR0000SA0'
headers = {'Content-type': 'application/json'}
data = json.dumps({"seriesid": ['CUUSA210SA0'],"startyear":"2018", "endyear":"2021"})
p = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=data, headers=headers)
json_data = json.loads(p.text)
for series in json_data['Results']['series']:
    x=prettytable.PrettyTable(["series id","year","period","value","footnotes"])
    seriesId = series['seriesID']
    print( series['data'])
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
    output = open(seriesId + '.txt','w')
    output.write (x.get_string())
    output.close()