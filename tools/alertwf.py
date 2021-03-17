import requests, shutil
from datetime import datetime
import pandas as pd # type: ignore
from typing import List, Dict, Any

def get_metadata() -> Dict[str, Any]:
    URL = 'https://s3-us-west-2.amazonaws.com/alertwildfire-data-public/all_cameras-v2.json'
    REF = 'https://www.alertwildfire.org'

    result = requests.get(URL, headers={'referer': REF, 'origin': REF, 'connection': 'keep-alive'})
    assert result.status_code == 200, ("Error requesting metadata: %d"%result.status_code)
    return result.json()

def get_station_list() -> List[str]:
    data = get_metadata()
    return [station['properties']['id'] for station in data['features']]

def get_all_cameras() -> object:
    '''
    Fetch metadata for all cameras.
    '''
    data = get_metadata()
    cameras = pd.json_normalize(data['features'])
    cameras.columns = [s.replace('properties.', '') for s in cameras.columns]
    cameras.set_index('id', inplace=True)

    coords = pd.DataFrame(cameras['geometry.coordinates'].apply(pd.to_numeric).to_list(),
                          columns=['longitude','latitude','elevation_km'], index=cameras.index)
    cameras = cameras.merge(coords, on='id')
    cameras['fov_rt'] = cameras['fov_rt'].apply(pd.to_numeric)
    cameras['fov_lft'] = cameras['fov_lft'].apply(pd.to_numeric)
    cameras['fov_center'] = cameras['fov_center'].apply(pd.to_numeric)
    cameras['last_movement_at'] = cameras['last_movement_at'].apply(pd.to_datetime)
    now = datetime.now()
    cameras['lastupdate'] = cameras['lastupdate'].apply(lambda dt: now - pd.to_timedelta(dt, unit='s'))

    drop_cols = ['type', 'attribution', 'sponsor', 'isp', 'network', 'county', \
                 'region', 'geometry.type', 'geometry.coordinates']
    cameras.drop(drop_cols, axis='columns', inplace=True, errors='ignore')

    return cameras

#cameras = get_all_cameras()

def get_latest_image(station_id: str, dest: str) -> None:
    '''
    Download latest image from a station and dump it in
    its native jpg format directly to a file.
    '''
    assert dest.lower().endswith('.jpg')

    URL = f'https://s3-us-west-2.amazonaws.com/alertwildfire-data-public/{station_id}/latest_full.jpg'
    URL += f'?x-request-time={int(datetime.now().timestamp())}'
    hdrs = {
        'referer':'https://www.alertwildfire.org',
        'origin':'https://www.alertwildfire.org',
        'accept':'image/webp,*/*',
        'accept-language':'en,en-GB;q=0.5',
        'accept-encoding':'gzip, deflate',
        'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0'
    }
    result = requests.get(URL, headers=hdrs, stream=True)

    assert result.status_code == 200, ("Error requesting image: %d"%result.status_code)

    with open(dest,'wb') as latest_img:
        result.raw.decode_content = True
        shutil.copyfileobj(result.raw, latest_img)

#get_latest_image('Axis-Brightwood', 'latest_axis.jpg')