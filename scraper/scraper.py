import sys
import requests
import time
from bs4 import BeautifulSoup
import argparse
import random
import os

class scraper:
         
    def path_to_url(self, path):
        return 'http://sfbay.craigslist.org'+path

    #def pathlist_to_urllist(self, path_list):
    #    return map(lambda x: 'http://sfbay.craigslist.org/'+x, path_list)

    def __init__(self, args):
        self.region = args.region
        self.page_delay = args.page_delay
        self.page_limit = args.page_limit
        self.do_simulate = args.do_simulate
        self.infiles = args.infiles 
        self.data_dir = args.data_dir

    def download_listings(self, path_list):
        count = 0
        for path in path_list:
            url = self.path_to_url(path)
            filename = self.data_dir + path
            if self.do_simulate:
                print "Simulating downloading " + url + " and saving to " + filename
            else:
                print "Downloading " + url + " and saving to " + filename
                # already downloaded, skip
                if os.path.exists(filename):
                    continue

                # Try 10 times
                for i in range(10):
                    try:
                        resp = requests.get(url)
                        break
                    except:
                        print "WARNING: URL requests has problem."
                        if i == 9:
                            raise
                        print "Retry URL in ", 2<<i, "seconds ..."
                        time.sleep( 2<<i )
                
                bytes = resp.content
                # e.g., <span class='range'>1 - 100</span> of <span class="totalcount">181</span> 
                # create parent dirs if needed
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))
                with open(filename, 'w') as outfile:
                    outfile.write(bytes)

            # slow down the downloads
            rand_delay = 2.0 + random.expovariate(1.0/self.page_delay)
            print "Sleeping ", rand_delay, "seconds ..."
            time.sleep(rand_delay)

            # dont download too much
            count += 1 
            if count >= self.page_limit:
                break


    def extract_listings(self):
        path_list = []
        for f in self.infiles:
            bytes = f.read()
            parsed = BeautifulSoup(bytes)
            listings = parsed.find_all('p', class_='row')
            print "No. of listings = ", len(listings)
            # index page looks broken
            if (len(listings) == 0):
                continue
 
            for listing in listings:
                 # if we can find an URL, add to list
                 path = self.parse_listing(listing)
                 if (path):
                     path_list.append(path)

        # Print the list of URLs  
        return path_list

    def parse_listing(self, listing):
        try:
            #print(listing.prettify())
            #house_type = listing.find('span', class_='housing').text
            #price = listing.find('span', class_='price').text
            #area = listing.find('span', class_='pnr').find('small').text
            #housing = listing.find('span', class_='housing').text
            path = listing.find('a', class_='i')['href']
            #print area, "|", price, "|", house_type
        except:
            print("Parsing error:", sys.exc_info()[0])
            print(listing.prettify())
            path = None
        return path

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Download listing pages')

    parser.add_argument("-g", dest='region', help='Region such as eby sby etc.')
    parser.add_argument("-d", dest='data_dir', default="./data", help="Base dir of data")

    parser.add_argument("-y", dest='page_delay', type=float, default=2.0, help='Delay (in secs) between requests')
    parser.add_argument("-l", dest='page_limit', type=int, default=2500, help='Limit number of listings to pull')
    parser.add_argument("-n", dest='do_simulate', action='store_true', help="Don't actually download, just simulate.")
    parser.add_argument(dest='infiles', nargs='+', type=argparse.FileType('r'),
                        metavar='index_html', help='index HTML file to parse and scrape')

    parsed_args = parser.parse_args()
    scraper = scraper(args=parsed_args)

    # Extract list of links to download
    path_list = scraper.extract_listings()
    print len(path_list)

    # Download the links that haven't been downloaded
    scraper.download_listings(path_list)
 
