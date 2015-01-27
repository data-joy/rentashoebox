import sys
import argparse


class addr_utils:

    def parse_cities_list(self, filename):
        with open(filename, 'r') as f:
            for line in f.readlines():
                city_name = line.rstrip() 
                if (city_name):
                    self.cities_list.append(city_name.lower())
  
    def extract_cities(self, text):
        extracted_list = []
        text_lc = text.lower()
        for city in self.cities_list:
            if city in text_lc:
                extracted_list.append(city)
        return extracted_list

    def print_cities_list(self):
        print self.cities_list

    def __init__(self):
        self.cities_list = []



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Various utilities')
    parser.add_argument("-c", dest='cities_file', help="Names of cities, one line each.")

    parser.add_argument("-C", dest='city_query_string', help="Blob with city name")

    #parser.add_argument("-d", dest='indir', help="Directory where HTML files are stored.")

    #parser.add_argument(dest='infiles', nargs='*', type=argparse.FileType('r'),
    #                    metavar='listing_html', help='listing HTML file to parse and scrape')

    args = parser.parse_args()

    utils = addr_utils()
    if args.cities_file:
        # Extract list of links to download
        utils.parse_cities_list(args.cities_file)
        utils.print_cities_list()

    if args.city_query_string:
        cities = utils.extract_cities(args.city_query_string)
        print cities
        
 
    
