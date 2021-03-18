#!/usr/bin/env python3

import json, os
import sqlalchemy as SQL # type: ignore
from urllib.parse import quote_plus
from typing import Dict, Any

def get_sql_engine() -> object:
    home = os.path.expanduser('~')
    secrets_path = os.path.join(home, 'Documents', 'secrets.json')
    with open(secrets_path,'r') as secrets_file:
        secrets = json.load(secrets_file)
        _sql_secrets = secrets['mysql']
        sql_passwd = quote_plus(_sql_secrets['PASSWD'])
        sql_usr = _sql_secrets['USER']
        sql_host = _sql_secrets['HOST']
        sql_port = _sql_secrets['PORT']
        sql_db = _sql_secrets['DB']

    url = f"mysql+pymysql://{sql_usr}:{sql_passwd}@{sql_host}:{sql_port}/{sql_db}"
    return SQL.create_engine(url)
