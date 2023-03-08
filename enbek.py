import re
import json
import urllib3
import time
from bs4 import BeautifulSoup

start_time = time.time()
url = "https://www.enbek.kz/ru/search/vac?page="
links = []

http = urllib3.PoolManager()

for i in range(1, 2):
    response = http.request("GET",  url+str(i))

    soup = BeautifulSoup(response.data)

    data = soup.find("div", {"class": "col-lg-8 col-xxl-9"})
    data = data.find_all("div", {"class": "item-list"})
    
    for i in data:
        d = i.find("a", {"href": True})
        links.append(d.get("href"))
        
uniqueLinks = tuple(set(links))
data = []

class LazyDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        regex_replacements = [
            (re.compile(r'([^\\])\\([^\\])'), r'\1\\\\\2'),
            (re.compile(r',(\s*])'), r'\1'),
        ]
        for regex, replacement in regex_replacements:
            s = regex.sub(replacement, s)
        return super().decode(s, **kwargs)

url = "https://www.enbek.kz"

for i in uniqueLinks:
    try:
        http = urllib3.PoolManager()
        response = http.request("GET",  url+i)

        soup = BeautifulSoup(response.data)

        d={}
        u = str(url+i)

        title = soup.find("h4", {"class": "title"}).get_text().strip()
        d['title'] = title
        subtitle = soup.find("div", {"class": "subtitle mb-2"})
        if (subtitle is not None and subtitle != ""):
            d['subtitle'] = subtitle.get_text().strip()

        category = soup.find("div", {"class": "category mb-2"}).get_text().strip()
        price = {}

        priceString = soup.find("div", {"class": "price"}).get_text().strip()

        pattern = r'от\s+(\d[\d\s]*)\s+до\s+(\d[\d\s]*)\s+тенге'
        # pattern = r'(\d[\d\s]*)\s+бастап\s+(\d[\d\s]*)\s+теңгеге дейін'
        pattern2 = r'от\s+(\d[\d\s]*)\s+тенге'

        matches = re.findall(pattern, priceString)
        if (matches):
            price1 = int(matches[0][0].replace(' ', ''))
            price2 = int(matches[0][1].replace(' ', ''))
            price['от'] = price1    
            price['до'] = price2
            # price.append(price2)
        else:
            match = re.findall(pattern2, priceString)
            price1 = int(match[0].replace(' ', ''))
            price['от'] = price1

        param = soup.find_all("ul", {"class": "info d-flex flex-column"})

        keysLst = []
        valuesLst = []
        for p in param:
            keys = p.find_all("span", {"class": "label"})
            for i in keys:
                keysLst.append(i.get_text().strip())

            values = p.find_all("span", class_=False)
            for i in values:
                valuesLst.append(i.get_text().strip())

        vacancyInfo = dict(zip(keysLst, valuesLst))


        jsdata = soup.find("script", {"type": "application/ld+json"})
        offers = jsdata.contents[0][jsdata.contents[0].find("{"): jsdata.contents[0].rfind("}") + 1]
        offers = json.loads(offers, cls=LazyDecoder)

        keys = ["hiringOrganization", "jobLocation", "aggregateRating"]
        offers = {i: offers[i] for i in keys if i in offers}

        amount = soup.find("div", {"class": "single-line"})
        amount = int(amount.find("div", {"class": "value"}).get_text().strip())


        # final data
        # print("final")

        d['category'] = category
        d['positionNo'] = amount
        d['salary'] = price
        d['url'] = u
        d['info'] = vacancyInfo
        d.update(offers)
        data.append(d)
    except:
        print("invalid json format --- skip")

with open("enbek.json", "w") as outfile:
    json.dump(data, outfile)

print("--- done in %s mins ---" % ((time.time() - start_time)/60))
# print("invalid json format --- url: %s" % url+i)