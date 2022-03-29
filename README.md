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
BooksAll.2016.part01.utf8
BooksAll.2016.part02.utf8
BooksAll.2016.part03.utf8
BooksAll.2016.part04.utf8
BooksAll.2016.part05.utf8
...
```

**Import the first 10 records from one file:**

    ./bulk-import.py -n 10 -f BooksAll.2016.part01.utf8 marc_loc_2016

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
                      [-o OFFSET] [-l] [-d] [-s]
                      [item]

Bulk MARC importer.

positional arguments:
  item                  Source item containing MARC records

optional arguments:
  -h, --help            show this help message and exit
  -i, --info            List available MARC21 .mrc files on this item
  -b [BARCODE], --barcode [BARCODE]
                        Barcoded local_id available for import
  -f FILE, --file FILE  Bulk MARC file to import
  -n NUMBER, --number NUMBER
                        Number of records to import
  -o OFFSET, --offset OFFSET
                        Offset in BYTES from which to start importing
  -l, --local           Import to a locally running Open Library dev instance
                        for testing (localhost:8080)
  -d, --dev             Import to dev.openlibrary.org Open Library dev
                        instance for testing
  -s, --staging         Import to staging.openlibrary.org Open Library staging
                        instance for testing
```
