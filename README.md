# ia-bulkmarc-importer

Command line tool for importing bulk MARC records from [archive.org](https://archive.org) data items into [Open Library](https://openlibrary.org)
using the MARC import API endpoint: [/api/import/ia](https://github.com/internetarchive/openlibrary/wiki/Endpoints#import-by-archiveorg-reference)

[Data items](https://archive.org/details/ol_data) on [archive.org](https://archive.org) can contain one or more files
of bibliographic collection data in MARC21 format. This tool takes an [archive.org](https://archive.org) item identifier and a specific filename
stored on that item using the `-f` parameter. It will then send a series of requests to [openlibrary.org](https://openlibrary.org)
to import individual MARC records in sequence, keeping track of the current offset in the collection file.

## Example Usage

**List importable MARC21 data files on an item:**

    ./bulk-import.py -i marc_loc_2016

*Output:*
```
Importing to https://openlibrary.org
ITEM: marc_loc_2016
FILENAME: None
Item marc_loc_2016 has the following MARC files:
BooksAll.2016.part01.utf8 241731867
BooksAll.2016.part02.utf8 205067420
BooksAll.2016.part03.utf8 197959817
BooksAll.2016.part04.utf8 182904720
BooksAll.2016.part05.utf8 174132979
...
BooksAll.2016.part43.utf8  27314711
```

**Import the first 10 records from one file:**

    ./bulk-import.py -n 10 -f BooksAll.2016.part01.utf8 marc_loc_2016

*Output:*
```
Importing to https://openlibrary.org
ITEM: marc_loc_2016
FILENAME: BooksAll.2016.part01.utf8
marc_loc_2016/BooksAll.2016.part01.utf8:0:5: 200 -- {'success': True, 'edition': {'key': '/books/OL6773974M', 'status': 'matched'}, 'work': {'key': '/works/OL7794899W', 'status': 'matched'}, 'next_record_offset': 720, 'next_record_length': 720}
marc_loc_2016/BooksAll.2016.part01.utf8:720:720: 200 -- {'success': True, 'edition': {'key': '/books/OL6773975M', 'status': 'matched'}, 'work': {'key': '/works/OL2337971W', 'status': 'matched'}, 'next_record_offset': 1440, 'next_record_length': 472}
marc_loc_2016/BooksAll.2016.part01.utf8:1440:472: 200 -- {'success': True, 'edition': {'key': '/books/OL6773976M', 'status': 'matched'}, 'work': {'key': '/works/OL2986881W', 'status': 'matched'}, 'next_record_offset': 1912, 'next_record_length': 548}
marc_loc_2016/BooksAll.2016.part01.utf8:1912:548: 200 -- {'success': True, 'edition': {'key': '/books/OL7126496M', 'status': 'matched'}, 'work': {'key': '/works/OL6800791W', 'status': 'matched'}, 'next_record_offset': 2460, 'next_record_length': 483}
marc_loc_2016/BooksAll.2016.part01.utf8:2460:483: 200 -- {'success': True, 'edition': {'key': '/books/OL6773978M', 'status': 'matched'}, 'work': {'key': '/works/OL69146W', 'status': 'matched'}, 'next_record_offset': 2943, 'next_record_length': 708}
marc_loc_2016/BooksAll.2016.part01.utf8:2943:708: 200 -- {'success': True, 'edition': {'key': '/books/OL6773979M', 'status': 'matched'}, 'work': {'key': '/works/OL1287294W', 'status': 'matched'}, 'next_record_offset': 3651, 'next_record_length': 631}
marc_loc_2016/BooksAll.2016.part01.utf8:3651:631: 200 -- {'success': True, 'edition': {'key': '/books/OL6773980M', 'status': 'matched'}, 'work': {'key': '/works/OL7713813W', 'status': 'matched'}, 'next_record_offset': 4282, 'next_record_length': 712}
marc_loc_2016/BooksAll.2016.part01.utf8:4282:712: 200 -- {'success': True, 'edition': {'key': '/books/OL6773981M', 'status': 'matched'}, 'work': {'key': '/works/OL543756W', 'status': 'matched'}, 'next_record_offset': 4994, 'next_record_length': 614}
marc_loc_2016/BooksAll.2016.part01.utf8:4994:614: 200 -- {'success': True, 'edition': {'key': '/books/OL6773982M', 'status': 'matched'}, 'work': {'key': '/works/OL220879W', 'status': 'matched'}, 'next_record_offset': 5608, 'next_record_length': 785}
marc_loc_2016/BooksAll.2016.part01.utf8:5608:785: 200 -- {'success': True, 'edition': {'key': '/books/OL6773983M', 'status': 'matched'}, 'work': {'key': '/works/OL1643985W', 'status': 'matched'}, 'next_record_offset': 6393, 'next_record_length': 886}
```

The MARC record can be viewed online by pre-pending `https://openlibrary.org/show-records/` to the `<item>/<file>:<offset>:<length>` record identifier, e.g. for the 10th record above:

https://openlibrary.org/show-records/marc_loc_2016/BooksAll.2016.part01.utf8:5608:785

**(Re-)import a single record from an offset within a MARC21 collection file:**

    ./bulk-import.py -o9068136 -n1 -f BooksAll.2016.part43.utf8 marc_loc_2016

*Output:*
```
Importing to https://openlibrary.org
ITEM: marc_loc_2016
FILENAME: BooksAll.2016.part43.utf8
marc_loc_2016/BooksAll.2016.part43.utf8:9068136:5: 200 -- {'success': True, 'edition': {'key': '/books/OL2449M', 'status': 'matched'}, 'work': {'key': '/works/OL22305878W', 'status': 'matched'}, 'next_record_offset': 9068603, 'next_record_length': 542}
```

The JSON response shows the item has been matched and no further changes were made. The `next_record_offset` value, `9068603`, is the offset of the next MARC record in the collection which is used to import the next record when `-n` is greater than one.

**Full Usage and Help:**

    ./bulk-import.py -h

*Output:*
```
usage: bulk-import.py [-h] [-i] [-b [BARCODE]] [-f FILE] [-n NUMBER]
                      [-o OFFSET] [-l] [-t] [-s]
                      [item]

Bulk MARC importer.

positional arguments:
  item                  Source item containing MARC records

optional arguments:
  -h, --help            show this help message and exit
  -i, --info            List item's available MARC21 .mrc files with size in
                        bytes
  -b [BARCODE], --barcode [BARCODE]
                        Barcoded local_id available for import
  -f FILE, --file FILE  Bulk MARC file to import
  -n NUMBER, --number NUMBER
                        Number of records to import
  -o OFFSET, --offset OFFSET
                        Offset in BYTES from which to start importing
  -l, --local           Import to a locally running Open Library dev instance
                        for testing (localhost:8080)
  -t, --testing         Import to testing.openlibrary.org Open Library
                        instance for testing
  -s, --staging         Import to staging.openlibrary.org Open Library staging
                        instance for testing
```
