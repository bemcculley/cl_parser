import requests
from bs4 import BeautifulSoup as bs4
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class cl_apartment(object):


    def __init__(self):

        scope = ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
        gc = gspread.authorize(credentials)
        self.wks = gc.open_by_key("1h1nOWYI2VVMxHDHfnd6YMeCQlICd2tOY6DzR5mbpjY").sheet1

        self.url = 'http://denver.craigslist.org/search/apa'
        self.apartment = {}

    def main(self):
        params = dict(pets_cat=1, max_price=2000)
        rsp = requests.get(self.url, params=params)
        html = bs4(rsp.text, 'html.parser')
        apts = html.find_all('p', attrs={'class': 'row'})
        for apt in apts:
            #    print apt.prettify()
            size = apt.findAll(attrs={'class': 'housing'})[0].text
            sqft, beds = self.find_size_and_bdrms(size)
            self.apartment['sqft'] = sqft
            self.apartment['beds'] = beds
            self.apartment['updated_datetime'] = apt.find('time')['datetime']
            self.apartment['price'] = float(apt.find('span', {'class': 'price'}).text.strip('$'))
            self.apartment['title'] = apt.find('a', attrs={'class': 'hdrlnk'}).text
            self.apartment['url'] = 'h'+self.url.strip('/search/apa') + apt.find('a', attrs={'class': 'hdrlnk'})['href']
            info = self.get_more_info(self.apartment['url'])
            

            for k,v in self.apartment.iteritems():
                print k,v
            print '\n'

            exit()
            time.sleep(1)


    def save_to_sheet(self, data):
        count = 0
        for k in data.iterkeys():
            self.wks.update_acell('%s1' % chr(97) + count, k )
            count += 1
        

    def find_size_and_bdrms(self,size):
        split = size.strip('/- ').split(' - ')
        if len(split) == 2:
            n_brs = split[0].replace('br', '')
            this_size = split[1].replace('ft2', '')
        elif 'br' in split[0]:
            # It's the n_bedrooms
            n_brs = split[0].replace('br', '')
            this_size = 0
        elif 'ft2' in split[0]:
            # It's the size
            this_size = split[0].replace('ft2', '')
            n_brs = 0
        return float(this_size), float(n_brs)

    def get_more_info(self, info_url):
        rsp = requests.get(info_url)
        html = bs4(rsp.text, 'html.parser')
        details = self.get_details(html)
        amenities = self.get_amenities(html)

    def get_details(self, html):
        details = html.find(id='postingbody').text.lower().split('\n')
        self.apartment['description'] = details[1].strip()
        for item in details:
            if 'view' in item:
                self.apartment['view'] = item

    def get_amenities(self,html):
        amenities = {}
        count = 0
        for attrs in html.find_all('p',attrs={'class':'attrgroup'})[-1]:
            count += 1          
            attrs = str(attrs).replace('</span>','')
            attrs = attrs.replace('</br>','')
            attrs = attrs.replace('<br/>','')
            attrs = attrs.replace('<br>','').split('<span>')
            for attr in attrs:
                if 'w/d' in attr or 'laundry' in attr:
                    self.apartment['w/d'] = attr
                if 'garage' in attr or 'car' in attr or 'parking' in attr:
                    self.apartment['parking'] = attr
                if 'apartment' in attr or 'plex' in attr or 'condo' in attr:
                    self.apartment['building_type'] = attr
            
cl_apartment().main()
