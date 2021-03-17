#!/usr/bin/env python3

import boto3 # type: ignore
import io, json, os, shutil, subprocess, time
from datetime import datetime, timezone, timedelta

from tools.imgtools import get_exif, get_timestamp
from tools.alertwf import get_station_list, get_all_cameras, get_latest_image

from typing import List, Optional

class Scraper():
    def __init__(self, stations: List[str], destdir: str, \
                tmpdir: Optional[str]='/tmp', \
                quiet: Optional[bool]=False) -> None:
        self.dest = destdir
        self.tmpdir = tmpdir
        self.quiet = quiet

        self.save_to_s3 = self.dest.startswith('s3://')
        if self.save_to_s3:
            self.s3 = boto3.client('s3')
            bucket, key = self.dest[5:].split('/',1)
            while key.endswith('/'):
                key = key[:-1]
            self.bucket = bucket
            self.basekey = key
        else:
            self.mddir = os.path.join(self.dest, 'metadata')
            if not os.path.exists(self.mddir):
                os.makedirs(self.mddir)
            assert os.path.isdir(self.mddir)

        _t0 = datetime.fromisoformat('1970-01-01T00:00:00+00:00')
        self.stations = dict()
        for st in stations:
            base = st.split('-',1)[-1]
            tmppath = os.path.join(tmpdir, base+'.jpg')
            self.stations[st] = dict(i=0, base=base, tmp=tmppath, last=_t0)

            if not self.save_to_s3:
                dest = os.path.join(self.dest, base)
                if not os.path.exists(dest):
                    os.makedirs(dest)
                assert os.path.isdir(dest)

        if not self.quiet:
            print('Image path example:\n')
            now = datetime.now().isoformat()
            base = self.stations[stations[0]]['base']
            if self.save_to_s3:
                print(f"    s3://{self.bucket}/{self.basekey}/{base}/{base}_{now}.jpg")
            else:
                print(f"    {self.dest}/{base}/{base}_{now}.jpg")
            print('\nProgress:\n')


    def capture(self) -> List[str]:
        metadata = get_all_cameras()
        metadata['latest'] = ''
        metadata['exif'] = ''

        write_md = False
        msgs = []
        for name in self.stations:
            msg = ''
            try:
                st = self.stations[name]
                base = st['base']

                tmpimg = os.path.join(self.tmpdir, f'{base}.jpg')
                tmpsmall = os.path.join(self.tmpdir, f'small-{base}.jpg')

                get_latest_image(name, tmpimg)
                subprocess.call(['convert', tmpimg, '-resize', '@250000', tmpsmall],
                                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

                exif = get_exif(tmpimg)
                ts = get_timestamp(exif, method='exif')
                if ts > st['last']:
                    fname = f"{base}_{ts.isoformat()}.jpg"
                    fnamesmall = f"{base}_{ts.isoformat()}-small.jpg"
                    if self.save_to_s3:
                        with open(tmpimg,'rb') as src:
                            key = f"{self.basekey}/{base}/{fname}"
                            self.s3.put_object(Bucket=self.bucket, Key=key, Body=src)
                        with open(tmpsmall,'rb') as src:
                            key = f"{self.basekey}/{base}/{fnamesmall}"
                            self.s3.put_object(Bucket=self.bucket, Key=key, Body=src)
                    else:
                        shutil.move(tmpimg,   os.path.join(self.dest, base, fname))
                        shutil.move(tmpsmall, os.path.join(self.dest, base, fnamesmall))

                    write_md = True
                    metadata.loc[name,'latest'] = ts
                    metadata.loc[name,'exif'] = json.dumps(exif)
                    self.stations[name]['i'] += 1
                    self.stations[name]['last'] = ts

                msg = '%04d '%self.stations[name]['i']
                msg += name.ljust(30)[:30]
                msg += ': ' + ts.isoformat()
            except Exception as e:
                msg = ('%04d Error (%s): '%(self.stations[name]['i'], name)) + str(e)

            msgs.append(msg)

        if write_md:
            now = datetime.now().isoformat()
            metadata = metadata[metadata.latest != '']
            if self.save_to_s3:
                bio = io.BytesIO()
                metadata.to_csv(bio)
                key = f"{self.basekey}/metadata/cameras_{now}.csv"
                self.s3.put_object(Bucket=self.bucket, Key=key, Body=bio.getvalue())
            else:
                metadata.to_csv(f"{self.mddir}/cameras_{now}.csv")

        return msgs

    def run(self, delay: float, limit: Optional[int]=None):
        i = 0
        while not os.path.exists('terminate'):
            i += 1
            msgs = self.capture()

            if self.quiet:
                now = datetime.now(tz=timezone(timedelta(hours=-7)))
                next = now + timedelta(seconds=delay)
                print('%05d'%i, 'Last:',now.ctime(), 'Next:', next.ctime(), end='\r')
            else:
                for msg in msgs:
                    term = 80
                    msg = ('  ' + msg).ljust(term)
                    if len(msg) > term:
                        msg = msg[:term-3]+'...'
                    print(msg)
                os.write(1, b"\x1b[%dF"%len(msgs))

            if limit is None or i < limit:
                time.sleep(delay)
            else:
                break

        print('\n'*(0 if self.quiet else len(self.stations)))

        if os.path.exists('terminate'):
            print('Terminated upon request')
            os.remove('terminate')


if __name__ == '__main__':
    import pathlib
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-s', '--station', required=True, action='append',
                        help=('Name of a camera station, e.g. Axis-Brightwood. '
                            + 'Multiple station names may be specified, but at '
                            + 'least one is required.'))
    parser.add_argument('--delay', type=float, default=20,
                        help='Seconds between attempts to poll for new imagery.')
    parser.add_argument('--limit', type=int, default=None,
                        help='Maximum number of polling attempts.')
    parser.add_argument('--tmpdir', type=pathlib.Path, default='/tmp',
                        help=('Local directory in which to store downloaded images '
                            + 'before transferring them to the destination.'))
    parser.add_argument('--quiet', action='store_true', help='Suppress (most) output')
    parser.add_argument('dest', metavar='destination',
                        help=('Base path of destination. Files will be saved '
                            + 'relative to this directory in subfolders named '
                            + 'after each station.'))
    args = parser.parse_args()

    if args.dest.startswith('s3://'):
        dest = args.dest
    else:
        dest = os.path.abspath(os.path.expanduser(args.dest))

    stations = list(sorted(args.station))
    if 'all' in stations:
        stations = get_station_list()

    tmpdir = args.tmpdir.absolute()
    delay = args.delay
    limit = args.limit
    quiet = args.quiet

    if not quiet:
        print(f'''
        Scraping imagery for stations: {", ".join(stations)}
        Polling every: {delay} seconds
        Saving to base path: {dest}
        '''.replace('        ','    '))

    sc = Scraper(stations, dest, tmpdir, quiet)
    sc.run(delay, limit)
    if not quiet:
        print('\n'*len(stations))
        print('Done')