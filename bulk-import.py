#!/usr/bin/env python3

""" 
    Iterates over an archive.org bulk MARC item, such as OpenLibraries-Trent-MARCs,
    and imports all records in all of its MARC files to Open Library.

    USAGE: ./bulk-import.py <archive.org item id>

    Logs results to STDOUT
"""

import argparse
import internetarchive as ia
import os
import re
import sys
from collections import namedtuple
from olclient.openlibrary import OpenLibrary
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError
from glob import glob
from time import sleep


try:
    from simplejson.errors import JSONDecodeError
except ImportError:
    from json.decoder import JSONDecodeError


BULK_API = '/api/import/ia'
LOCAL_ID = re.compile(r'\/local_ids\/(\w+)')
MARC_EXT = re.compile(r'.*\.(mrc|utf8)$')

SERVER_ISSUES_WAIT = 50 * 60  # seconds to wait if server is giving unexpected 5XXs likely to be resolved in time
SHORT_CONNECT_WAIT =  5 * 60  # seconds
MAX_RETRIES = 20
CHECK_LEN = 2000
RECORD_TERMINATOR = b'\x1d'  # MARC21 record terminator byte


def get_marc21_files(item):
    return [f for f in ia.get_files(item) if MARC_EXT.match(f.name)]


def log_error(response):
    n = 0
    current_errors = glob('error*.html')
    for f in current_errors:
        n = max(n, 1 + int(re.search(r'[0-9]+', os.path.splitext(f)[0]).group(0)))
    name = 'error_%d.html' % n
    with open(name, 'w') as error_log:
        error_log.write(response.content.decode())
    return name


def next_record(identifier, ol):
    """
    identifier: '{}/{}:{}:{}'.format(item, fname, offset, length)
    """
    m = None
    retries = 0
    while retries < MAX_RETRIES and not m:
        sleep(SHORT_CONNECT_WAIT)
        current = ol.session.get(ol.base_url + '/show-records/' + identifier)
        retries += 1
        m = re.search(r'<a href="\.\./[^/]+/[^:]+:([0-9]+):([0-9]+)".*Next</a>', current.text)
    next_offset, next_length = m.groups()
    # Follow redirect to get actual length (next_length is always 5 to trigger the redirect)
    r = ol.session.head(ol.base_url + '/show-records/' + re.search(r'^[^:]*', identifier).group(0) + ':%s:%s' % (next_offset, next_length))
    next_length = re.search(r'[^:]*$', r.headers.get('Location', '5')).group(0)
    return int(next_offset), int(next_length)


def main():
    parser = argparse.ArgumentParser(description='Bulk MARC importer.')
    parser.add_argument('item', help='Source item containing MARC records', nargs='?')
    parser.add_argument('-i', '--info', help="List item's available MARC21 .mrc files with size in bytes", action='store_true')
    parser.add_argument('-b', '--barcode', help='Barcoded local_id available for import', nargs='?', const=True, default=False)
    parser.add_argument('-f', '--file', help='Bulk MARC file to import')
    parser.add_argument('-n', '--number', help='Number of records to import', type=int, default=1)
    parser.add_argument('-o', '--offset', help='Offset in BYTES from which to start importing', type=int, default=0)
    parser.add_argument('-l', '--local', help='Import to a locally running Open Library dev instance for testing (localhost:8080)', action='store_true')
    parser.add_argument('-d', '--delay', help='Delay (in ms) between import requests', type=int, default=0)
    parser.add_argument('-t', '--testing', help='Import to testing.openlibrary.org Open Library instance for testing', action='store_true')
    parser.add_argument('-s', '--staging', help='Import to staging.openlibrary.org Open Library staging instance for testing', action='store_true')

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    item = args.item
    fname = args.file
    local_testing = args.local
    dev_testing = args.testing
    staging_testing = args.staging
    barcode = args.barcode

    if local_testing:
        Credentials = namedtuple('Credentials', ['username', 'password'])
        local_dev = 'http://localhost:8080'
        c = Credentials('openlibrary@example.com', 'admin123')
        ol = OpenLibrary(base_url=local_dev, credentials=c)
    elif staging_testing:
        ol = OpenLibrary(base_url='https://staging.openlibrary.org')
    elif dev_testing:
        ol = OpenLibrary(base_url='https://testing.openlibrary.org')
    else:
        ol = OpenLibrary()

    print(f'Importing to {ol.base_url}')
    print(f'ITEM: {item}')
    print(f'FILENAME: {fname}')

    if args.info:
        if barcode is True:
            # display available local_ids
            print('Available local_ids to import:')
            r = ol.session.get(ol.base_url + '/local_ids.json')
            print(LOCAL_ID.findall(r.json()['body']['value']))
        if item:
            # List MARC21 files, then quit.
            print(f'Item {item} has the following MARC files:')
            marcs = get_marc21_files(item)
            width = marcs and len(str(max([f.size for f in marcs])))
            for f in marcs:
                print('\t'.join([f.name, str(f.size).rjust(width)]))
        ol.session.close()
        exit()

    limit = args.number  # If non-zero: a limit to only process this many records from each file.
    count = 0
    offset = args.offset
    length = 5  # We only need to get the length of the first record (first 5 bytes), the API will seek to the end.

    ol.session.mount('https://', HTTPAdapter(max_retries=10))

    if offset < 0:
        # Negative offset from EOF. We need to know the file size.
        marcs = get_marc21_files(item)
        [size] = (f.size for f in marcs if f.name == fname)
        offset += size
        print(f"File size = {size}. Using offset = {offset}.")

    if offset > 0:
        # Check we are at the start of a record, or find next record.
        offset -= 1
        url = f'https://archive.org/download/{item}/{fname}'
        r = ol.session.get(url, headers={'Range': f'bytes={offset}-{offset + CHECK_LEN}'})
        terminator = r.content.index(RECORD_TERMINATOR)
        offset += terminator + 1

    while length:
        if limit and count >= limit:
            # Stop if a limit has been set, and we are over it.
            break
        identifier = f'{item}/{fname}:{offset}:{length}'
        data = {'identifier': identifier, 'bulk_marc': 'true'}
        if barcode and barcode is not True:
            # A local_id key has been passed to import a specific local_id barcode.
            data['local_id'] = barcode
        try:
            if args.delay:
                sleep(args.delay / 1000)
            r = ol.session.post(ol.base_url + BULK_API + '?debug=true', data=data)
            r.raise_for_status()

        except HTTPError as e:
            result = {}
            status = r.status_code
            if status > 500:
                error_summary = ''
                # On 503: wait then retry.
                if r.status_code == 503:
                    length = 5
                    offset = offset  # Repeat current import.
                    sleep(SERVER_ISSUES_WAIT)
                    continue
            elif status == 500:
                # In debug mode 500s produce HTML with details of the error.
                m = re.search(r'<h1>(.*)</h1>', r.text)
                error_summary = m and m.group(1) or r.text
                # Write error log to file.
                error_log = log_error(r)
                print(f'UNEXPECTED ERROR {r.status_code}; [{error_summary}] WRITTEN TO: {error_log}')

                if length == 5:
                    # Two 500 errors in a row: skip to next record.
                    sleep(SHORT_CONNECT_WAIT)
                    offset, length = next_record(identifier, ol)
                    continue
                if m:  # A handled, debugged, and logged error; unlikely to be resolved by retrying later:
                    # Skip this record and move to the next
                    offset = offset + length
                else:
                    sleep(SERVER_ISSUES_WAIT)
                length = 5
                print(f'{offset}:{length}')
                continue
            else:  # 4xx errors should have json content; to be handled in default 200 flow.
                pass
        except ConnectionError as e:
            print(f'CONNECTION ERROR: {e.args[0]}')
            sleep(SHORT_CONNECT_WAIT)
            continue
        # Log results to STDOUT.
        try:
            result = r.json()
            offset = result.get('next_record_offset')
            length = result.get('next_record_length')
        except JSONDecodeError:
            result = r.content
        print(f'{identifier}: {r.status_code} -- {result}')
        count += 1


if __name__ == '__main__':
    main()
