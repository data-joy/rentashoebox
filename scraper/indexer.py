import sys
import requests
import time
from bs4 import BeautifulSoup
import argparse
import random
import os


class listing_index:
    def get_filename(self, region, city, page_num):
        filename = self.data_dir + "/index/"
        filename += self.region

        if (self.city):
            filename += "_" + self.city
        filename += time.strftime("_%Y%m%d_%H%M%S") + ("_%d" % page_num) + ".html"
        return filename

    def get_url(self, region, city, page_num):
        # download
        # construct URL and filename
        # e.g., http://sfbay.craigslist.org/search/eby/apa?s=100&query=apartments%20in%20fremont
        url = "http://sfbay.craigslist.org/search/" + region + "/apa"
        url += "?s=%d&" % ((page_num-1) * 100)
        if city:
            url += "query=apartments%20in%20" + city
        return url
         
    def __init__(self, args):
        self.region = args.region
        self.city = args.city
        self.page_delay = args.page_delay
        self.page_limit = args.page_limit
        self.data_dir = args.data_dir
 
        if args.index_filename:
            # read from file
            self.do_download = False
            self.do_simulate = False
            self.filename = args.index_filename
        else:
            self.do_download = True
            self.do_simulate = args.do_simulate
            # filename is determined at time of download 


    def download_parse_all(self):
        if not self.do_download:
            return

        self.page_current = 1
        self.page_is_last = False
        while self.page_current <= self.page_limit:
            self.download()
            self.parse()
            if self.page_is_last:
                break
            self.page_current += 1 
        
    def download(self):
        self.url = self.get_url(self.region, self.city, self.page_current) 
        self.filename = self.get_filename(self.region, self.city, self.page_current) 

        print "---------"
        
        if self.do_simulate:
            print "Simulating downloading " + self.url + " and saving to " + self.filename
        else:
            print "Downloading " + self.url + " and saving to " + self.filename
            resp = requests.get(self.url)

        rand_delay = random.expovariate(1.0/self.page_delay)
        print "Sleeping ", rand_delay, "seconds ..."
        time.sleep(rand_delay)

        if self.do_simulate:
            # simulated content
            bytes = self.filename + " simulated contents:" + self.url
        else:
            bytes = resp.content
            # e.g., <span class='range'>1 - 100</span> of <span class="totalcount">181</span> 
            if not os.path.exists(os.path.dirname(self.filename)):
                os.makedirs(os.path.dirname(self.filename))

            with open(self.filename, 'w') as outfile:
                outfile.write(bytes)


    def parse(self):
        if self.do_simulate:
            print "Read simulated contents from " + self.filename
            self.page_is_last = False
            return

        print "Reading index from " + self.filename
        with open(self.filename, "r") as f:
            # read from f
            bytes = f.read()

        parsed = BeautifulSoup(bytes)

        listings = parsed.find_all('p', class_='row')
        print "No. of listings = ", len(listings)

        # if it looks OK, keep parsing
        if len(listings) >= 1:
            range_text = parsed.find('span', class_='range').text
            total_text = parsed.find('span', class_='totalcount').text
            #print parsed.find('a', class_='button next')['href']

            self.page_is_last = (int(range_text.split(' ')[2]) >= int(total_text))
            #print range_text, int(range_text.split(' ')[2]), total_text, self.page_is_last
        else:
            self.page_is_last = True

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download index pages')


    parser.add_argument("-g", dest='region', default='eby', help='Only scrape listings in specified region')
    parser.add_argument("-c", dest='city', default=None, help='Only scrape listings in specified city')

    parser.add_argument("-d", dest='data_dir', default="./data", help="Base dir of data")
    parser.add_argument("-r", dest='index_filename', help="read index page from file and parse")

    parser.add_argument("-y", dest='page_delay', type=float, default=3.0, help='Delay (in secs) between requests')
    parser.add_argument("-l", dest='page_limit', type=int, default=25, help='Limit number of index pages to pull')
    parser.add_argument("-n", dest='do_simulate', action='store_true', help="Don't actually download, just simulate.")

    parsed_args = parser.parse_args()

    index = listing_index(args=parsed_args)

    # if read from file, just parse it
    if parsed_args.index_filename:
        index.parse()
    else:
        # download all subject to page limit and parse
        index.download_parse_all()

