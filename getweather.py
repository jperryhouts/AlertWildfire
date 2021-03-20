#!/usr/bin/env python3

'''
Fetching weather data from openweathermap.org
'''

import json, os, requests, sys, time
import sqlalchemy # type: ignore
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from typing import Dict, Any

WEATHER_API = 'https://api.openweathermap.org/data/2.5/onecall/timemachine'

def get_hourly_weather(lon:float, lat:float, date:datetime, api_key: str) -> Dict[str,Any]:
    dt = str(int(date.timestamp()))
    prm = dict(lon=str(lon),lat=str(lat),dt=str(dt),units='metric',appid=api_key)
    result = requests.get(WEATHER_API, params=prm)
    assert result.status_code == 200, \
        f'status code: {result.status_code}\nURL: {result.url}'
    time.sleep(1) ## Rate-limited API
    return result.json()

def days_ago(n: int) -> datetime:
    d = datetime.date(datetime.today())-timedelta(days=n)
    dt = datetime.fromordinal(d.toordinal())
    return dt

if __name__ == '__main__':
    ## Initialize constant variables, and ensure destination
    ## path exists.
    HOME = os.path.expanduser('~')
    WEATHER_DIR = os.path.join(HOME, 'Data', 'Storage', 'AlertWF', 'weather')

    if not os.path.exists(WEATHER_DIR):
        os.makedirs(WEATHER_DIR)
    assert os.path.isdir(WEATHER_DIR)

    ## Establish MySQL DB connection
    secrets_path = os.path.join(HOME, 'Documents', 'secrets.json')
    with open(secrets_path,'r') as secrets_file:
        secrets = json.load(secrets_file)
        api_key = secrets['openweathermap.org']['api_key']
        _sql_secrets = secrets['mysql']
        sql_passwd = quote_plus(_sql_secrets['PASSWD'])
        sql_usr = _sql_secrets['USER']
        sql_host = _sql_secrets['HOST']
        sql_port = _sql_secrets['PORT']
        sql_db = _sql_secrets['DB']
        sql_url = f"mysql+pymysql://{sql_usr}:{sql_passwd}@{sql_host}:{sql_port}/{sql_db}"
        sql_engine = sqlalchemy.create_engine(sql_url)

    ## Actually perform queries and download data
    query = ''' SELECT DISTINCT station, lon, lat FROM 
                stations st INNER JOIN images im
                ON st.id=im.station; '''
    with sql_engine.connect().execution_options(autocommit=True) as conn:
        results = conn.execute(query)
        for station, lon, lat in results.fetchall():
            #for n in range(5):
            for n in [1]:
                dt = days_ago(n)
                fname = f"{station}-{dt.strftime('%Y-%m-%d')}.json"
                path = os.path.join(WEATHER_DIR, fname)
                if not os.path.exists(path):
                    try:
                        weather = get_hourly_weather(lon, lat, dt, api_key)
                        if '-v' in sys.argv:
                            print('  Saving:', path)
                        with open(path, 'w') as data_file:
                            json.dump(weather, data_file)
                    except Exception as e:
                        print('Error saving',path,str(e))

    if '-v' in sys.argv:
        print('Done!')