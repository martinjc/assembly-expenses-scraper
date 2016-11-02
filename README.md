# assembly-expenses-scraper
A selenium based scraper for Welsh Assembly Members public expenses record

## Requirements

* selenium - to drive the web browser
* chromedriver - default assumes this is in the same folder as the script, if not, supply the path as a command line argument
* tqdm - for the lovely progress bars on the command line

## Usage

usage: expenses.py [-h] -y [YEARS [YEARS ...]] [-s START] [-t TO] [-p PAUSE]
                   [-d DRIVER]

required arguments:


-y [YEARS [YEARS ...]], --years [YEARS [YEARS ...]]
                      list of years to check


optional arguments:


  -h, --help            show this help message and exit

  -s START, --start START
                        month to start scraping from

  -t TO, --to TO        
                        month to scrape to

  -p PAUSE, --pause PAUSE
                        pause to add between requests to server (in seconds) -
                        default 1/3 of a second

  -d DRIVER, --driver DRIVER
                        path to the chromedriver
