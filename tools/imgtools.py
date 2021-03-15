import json, subprocess
from datetime import datetime

def get_exif(fname):
    sp = subprocess.Popen(f'exiftool -json {fname}', shell=True, stdout=subprocess.PIPE)
    result = sp.stdout.read().decode('ISO-8859-15')
    exif = json.loads(result)[0]
    return exif

def get_timestamp(src, method='fname'):
    exif = get_exif(src) if method == 'fname' else  src
    tzfmt = lambda tz: ('-' if tz < 0 else '+')+'%02d'%abs(tz)
    timestamp = f"{exif['DateTimeOriginal']}{tzfmt(exif['TimeZoneOffset'])}:00"
    return datetime.strptime(timestamp, r'%Y:%m:%d %H:%M:%S%z')