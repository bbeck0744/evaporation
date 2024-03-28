# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
from datetime import datetime
from datetime import timedelta  
import pandas as pd
import json
import numpy as np
import requests
import time
from pandas.plotting import register_matplotlib_converters
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from meteostat import Point, Daily
import pyet as pyet
import urllib.request
import urllib.error

from meteostat import Hourly

now = datetime.utcnow().replace(microsecond=0, second=0, minute=0)
start = now - timedelta(days=5)
now_string = now.strftime("%Y-%m-%d")
start_string = start.strftime("%Y-%m-%d")

print("still working")

# Get hourly data
data = Hourly('72658', start, now)
data = data.fetch()
data = data.reset_index()
data['Date'] = data['time'].dt.date


data_mean = data.groupby('Date').mean()
data_mean['wspd_m_s'] = data_mean['wspd'] * 1000 / 60 / 60
data_mean['pres_kpa'] = data_mean['pres'] * 0.1
data_min = data.groupby('Date').min()
data_max = data.groupby('Date').max()

meteo = pd.DataFrame({"tmean":data_mean["temp"],
                      "tmax":data_max["temp"],
                      "tmin":data_min["temp"],
                      "rhmax":data_max["rhum"],
                      "rhmin":data_min["rhum"],
                      "u2":data_mean["wspd_m_s"],
                      "pressure":data_mean['pres_kpa']})
meteo = meteo.reset_index()
meteo['datetime'] = pd.to_datetime(meteo['Date'], utc=True)

BaseURL = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/'

API_KEY="A82AJZCBRUUB22QS5GGNDQ8ME"
LOCATION='Minneapolis'
UNIT_GROUP="metric"

StartDate = start_string
EndDate= now_string
#JSON or CSV 
#JSON format supports daily, hourly, current conditions, weather alerts and events in a single JSON package
#CSV format requires an 'include' parameter below to indicate which table section is required
ContentType="json"

#include sections
#values include days,hours,current,alerts
Include="days"

#basic query including location
ApiQuery=BaseURL + LOCATION

#append the start and end date if present
if (len(StartDate)):
    ApiQuery+="/"+StartDate
    if (len(EndDate)):
        ApiQuery+="/"+EndDate

#Url is completed. Now add query parameters (could be passed as GET or POST)
ApiQuery+="?"

#append each parameter as necessary
if (len(UNIT_GROUP)):
    ApiQuery+="&unitGroup="+UNIT_GROUP

if (len(ContentType)):
    ApiQuery+="&contentType="+ContentType

if (len(Include)):
    ApiQuery+="&include="+Include

ApiQuery+="&key="+API_KEY

def getWeatherForecast():

    try:
            req = urllib.request.urlopen(ApiQuery)
    except:
            print("Could not read from:"+ApiQuery);
            return []
                
    rawForecastData = req.read()
    req.close()
    return json.loads(rawForecastData)
    
weatherForecast = getWeatherForecast();

days=weatherForecast['days'];

solarrad = pd.DataFrame(days)
solarrad['datetime'] = pd.to_datetime(solarrad['datetime'], utc=True)

solarrad = solarrad[['datetime', 'solarradiation']]

merged = pd.merge(meteo, solarrad, on="datetime")
merged['Date'] = pd.to_datetime(merged['Date'], utc=True)

merged.rename(columns = {'solarradiation':'rs', 'Date':'date'}, inplace = True)
del merged['datetime']
merged = merged.set_index('date')

merged['rs'] = merged['rs']*86400/1000000

tmean, tmax, tmin, rhmax, rhmin, wind, pressure, rs = [merged[col] for col in merged.columns]
lat = 40.49*np.pi/180

pe_fao56 = pyet.pm_fao56(tmean, wind, rs=rs, pressure=pressure, elevation=256.0, lat=lat, tmax=tmax, tmin=tmin, rhmax=rhmax, rhmin=rhmin)

export_df = pd.DataFrame(data=pe_fao56)

export_df.to_csv('evap.csv')