#!/usr/bin/env python3

'''
After images are scraped from the AlertWildfire website,
they are simply placed in an S3 bucket. Only very minor
transformation is applied (creating a resized copy, and
extracting their exif data). They need to be loaded into
the `images` database table separately.

This script handles that process in batch for any images
which have been added to the S3 bucket, but not yet
added to the database.

Run it from the command line with no arguments. It'll
do its thing.
'''

## Some constants
BUCKET_NAME = 'storage-9iudgkuqwurq6'
PREFIX = 'AlertWF'

import boto3, re
from datetime import datetime
from tools.db_util import get_sql_engine, SQL
s3_resource = boto3.resource('s3')

def do_load(Bucket:str, Prefix:str) -> None:
    n=0
    
    params = dict(stationid=SQL.String, time_stamp=SQL.DateTime, path=SQL.String)
    insert_image_query = SQL.text('''
            INSERT INTO images (`station`, `time_stamp`, `path`)
            VALUES (:stationid, :time_stamp, :path);
        ''').bindparams(*[SQL.bindparam(p, type_=t) for p,t in params.items()])

    regex_path = re.compile(r'([^/]*)/([^/]*.jpg)$')
    regex_date = re.compile(r'(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d-\d\d:\d\d)')

    engine = get_sql_engine()
    with engine.connect() as conn:
        img_res = conn.execute('SELECT path FROM images')
        img_paths = [record[0] for record in img_res.fetchall()]

        tx = conn.begin()
        
        bucket = s3_resource.Bucket(Bucket)
        for obj in bucket.objects.filter(Prefix=Prefix):
            if ('small' in obj.key) or (obj.key in img_paths):
                continue
            match = regex_path.search(obj.key)
            if match:
                station, fname = match.groups()
                stamp = regex_date.search(fname).groups()[0]

                dtstamp = datetime.fromisoformat(stamp)
                stationid = f'Axis-{station}'

                row = dict(stationid=stationid, time_stamp=dtstamp, path=obj.key)
                conn.execute(insert_image_query, row)

                n += 1
        tx.commit()
    print('Inserted', n, 'records')

if __name__ == '__main__':
    do_load(BUCKET_NAME, PREFIX)