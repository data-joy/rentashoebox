import sys
import requests
import time
from bs4 import BeautifulSoup
import argparse
import random
import os
import re

class loader:
         
    def path_to_url(self, path):
        return 'http://sfbay.craigslist.org'+path

    #def pathlist_to_urllist(self, path_list):
    #    return map(lambda x: 'http://sfbay.craigslist.org/'+x, path_list)

    def __init__(self, args):
        #self.region = args.region
        self.page_delay = args.page_delay
        self.page_limit = args.page_limit
        self.do_simulate = args.do_simulate
        self.infiles = args.infiles 
        #self.data_dir = args.data_dir

    def extract_listings(self):
        path_list = []
        for f in self.infiles:
            bytes = f.read()
            parsed = BeautifulSoup(bytes)
            #listings = parsed.find_all('p', class_='row')

            print "----------------"
            print f.name

            # Extract lat, long
            # e.g., <div id="map" class="viewposting" data-latitude="37.536908" 
            #        data-longitude="-121.998000" data-accuracy="0"></div>
            map = parsed.find('div', id="map")
            if map:
                print "lat =", map['data-latitude']
                print "lon =", map['data-longitude']

            # Extract price
            # <h2 class="postingtitle">
            #  <span class="star"></span>
            #  &#x0024;1695 / 1br - 560ft^2 - :::::: We have Gas Stoves :::::: (fremont / union city / newark)
            # </h2>
            postingtitle = parsed.find('h2', class_="postingtitle")
            if postingtitle:
                listing = []
                title = postingtitle.text
                price = re.search('(\$\d+)', title)
                #br = re.search(' (\d+)br', title)
                #ba = re.search(' (\d+)ba', title)
                #ft = re.search(' (\d+)ft\^2', title)
                #print title
                if not price:
                    continue
                print "price =", price.group(0)
                #print "#BR =", br
                #print "#BA =", ba
                #print "#FT =", ft
            else:
                # broken liseting, skip
                continue 


           
            # Extract #BR / # Bath / Size 
            # Extract Price / Size / 
            # e.g.,  <p class="attrgroup">
            #          <span><b>1</b>BR / <b>1</b>Ba</span> 
            #          <span><b>560</b>ft<sup>2</sup></span> 
            #          <span>apartment</span> 
            #          <span class="housing_movein_now property_date" date="2015-01-24" today_msg="available now">available jan 24</span><br>
            #          <span>laundry on site</span> 
            #          <span>carport</span><br>
            #          <span>cats are OK - purrr</span></p>
            #         <p class="attrgroup"></p>
 
            atg = parsed.find('p', class_='attrgroup')
            if not atg:
                continue

            atg_spans = atg.find_all('span')
            if not atg_spans:
                continue
            print atg_spans 
            # e.g., <span><b>2</b>BR / <b>2</b>Ba</span>, <span><b>946</b>ft<sup>2</sup></span>
            for span in atg_spans:
                m = re.search('<b>\d+</b>BR', span)
                if m:
                    print "# BR =", m.group(0)
                else:
                    m = re.search('<b>\d+</b>ft<sup>2</sup>', span)
                    print "Size =", m.group(0)

            atg = parsed.find('p', class_='attrgroup')

            atg_spans = atg.find_all('span')

            # e.g., <span><b>2</b>BR / <b>2</b>Ba</span>, <span><b>946</b>ft<sup>2</sup></span>
            for span in atg_spans:
                text = span.text
                print text

                m = re.search('\d+BR', text)
                if m:
                    nbr = int(m.group(0))
                    # Note: don't break yet because #Ba is next

                    m=re.search('\d+Ba', text)
                    if m:
                        nba = int(m.group(0))
                    continue
    
                m = re.search('\d+ft2', text)
                if m:
                    print "Size =", m.group(0)
                    continue

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

    #parser.add_argument("-d", dest='data_dir', default="./data", help="Base dir of data")
    parser.add_argument("-o", dest='output_file', default="data.csv", help="Output file")

    parser.add_argument("-y", dest='page_delay', type=float, default=2.0, help='Delay (in secs) between requests')
    parser.add_argument("-l", dest='page_limit', type=int, default=1, help='Limit number of index pages to pull')
    parser.add_argument("-n", dest='do_simulate', action='store_true', help="Don't actually download, just simulate.")
    parser.add_argument(dest='infiles', nargs='+', type=argparse.FileType('r'),
                        metavar='listing_html', help='listing HTML file to parse and scrape')

    parsed_args = parser.parse_args()

    loader = loader(args=parsed_args)

    # Extract list of links to download
    listings = loader.extract_listings()
    #print len(listings)

    # Download the links that haven't been downloaded
    #loader.save_listings(listings)
 
