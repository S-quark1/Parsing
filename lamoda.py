import json
import urllib3
import time
from bs4 import BeautifulSoup

start_time = time.time()

urls = ["https://www.lamoda.kz/c/355/clothes-zhenskaya-odezhda/?page=",
"https://www.lamoda.kz/c/477/clothes-muzhskaya-odezhda/?page=",
"https://www.lamoda.kz/c/1590/clothes-dlia-devochek/?page=",
"https://www.lamoda.kz/c/1589/clothes-dlia-malchikov/?page="]

links = []
for url in urls:
    for i in range(1, 52):

        http = urllib3.PoolManager()
        response = http.request("GET",  url+str(i))

        soup = BeautifulSoup(response.data)

        data = soup.find("div", {"class": "grid__catalog"})
        data = data.find_all("a", {"href": True})
        
        for i in data:
            links.append(i.get("href"))

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

url = "https://www.lamoda.kz"

for i in uniqueLinks:
    try:
        http = urllib3.PoolManager()
        response = http.request("GET",  url+i)

        soup = BeautifulSoup(response.data)

        jsdata = soup.find_all("script", {"type": "application/ld+json"})
        offers = jsdata[1].contents[0][jsdata[1].contents[0].find("{"): jsdata[1].contents[0].rfind("}") + 1]
        offers = json.loads(offers, cls=LazyDecoder)
        offers.pop("image")
        offers.pop("description")
        keys = ["offers", "category", "aggregateRating"]
        offers = {i: offers[i] for i in keys if i in offers}

        categories = soup.find_all("a", {"class": "x-link x-link__secondaryLabel"})
        categoryLst = [i.get_text().strip() for i in categories]
        categoryLst.pop(0)
        categoryLst.append(offers.pop("category").replace('&quot;', ''))

        brand = soup.find("span", {"class": "x-premium-product-title__brand-name"}).get_text().strip()
        name = soup.find("div", {"class": "x-premium-product-title__model-name"}).get_text().strip()

        # peopleRated = soup.find("div", {"class": "product-rating__count"})
        # if peopleRated is None:
        #     peopleRated = 0
        # else:
        #     peopleRated = int(peopleRated.get_text())

        titles = soup.find_all("span", {"class": "x-premium-product-description-attribute__name"})
        titlesLst = [i.get_text() for i in titles]

        values = soup.find_all("span", {"class": "x-premium-product-description-attribute__value"})
        valuesLst = [i.get_text() for i in values]

        descrJs = dict(zip(titlesLst, valuesLst ))


        # final data

        d={}
        d['name'] = name
        d['brand'] = brand
        # d['peopleRated'] = peopleRated
        d.update(offers)
        d['description'] = descrJs
        d['categories'] = categoryLst
        data.append(d)
    except:
        print("invalid json format --- skip")

with open("lamoda.json", "w") as outfile:
    json.dump(data, outfile)

print("--- done in %s mins ---" % ((time.time() - start_time)/60))