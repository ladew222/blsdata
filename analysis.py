import requests
import json
import pandas as pd
import googlemaps
import datetime
import numpy as np
from numpy import random
from math import radians, cos, sin, asin, sqrt
import seaborn as sn
import matplotlib.pyplot as plt

#inflation

#filt_ = df_counties[["SAH_02/01/2016","SAH_12/01/2015","SAH_10/01/2015","SAH_08/01/2015","SAH_06/01/2015","2015-05-31","2015-06-30","2015-07-31","2015-08-31","2015-09-30","ALUBE001","ALW1E001","ALZKE001","B19083"]]

bls_areas = pd.read_csv("./output/df_final.csv")
bls_areas.columns.get_loc("GeoName_")
bls_areas=bls_areas.dropna()
bls_areas_inf=bls_areas.iloc[:, np.r_[159:170, 44]]
bls_areas_inf=bls_areas.transpose()
new_header = bls_areas_inf.iloc[0] #grab the first row for the header
bls_areas_inf = bls_areas_inf[1:] #take the data less the header row
bls_areas_inf.columns = new_header #set the header row as the df h
bls_areas_inf=bls_areas_inf.transpose()
bls_areas_inf.plot();
### GDP
bls_areas = pd.read_csv("./output/df_final.csv")
bls_areas=bls_areas.dropna()
bls_areas=bls_areas.iloc[:, np.r_[2,160:170]]
bls_areas=bls_areas.transpose()
new_header = bls_areas.iloc[0] #grab the first row for the header
bls_areas = bls_areas[1:] #take the data less the header row
bls_areas.columns = new_header #set the header row as the df h
bls_areas=bls_areas.transpose()

import missingno as msno
msno.bar(bls_areas)