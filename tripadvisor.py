import asyncio
import json
import random
import string
from typing import List, TypedDict

import httpx
from loguru import logger as log
from bs4 import BeautifulSoup
import pandas as pd
import requests


class LocationData(TypedDict):
    """result dataclass for tripadvisor location data"""

    localizedName: str
    url: str
    HOTELS_URL: str
    ATTRACTIONS_URL: str
    RESTAURANTS_URL: str
    placeType: str
    latitude: float
    longitude: float


async def scrape_location_data(query: str, client: httpx.AsyncClient) -> List[LocationData]:
    """
    scrape search location data from a given query.
    e.g. "New York" will return us TripAdvisor's location details for this query
    """
    log.info(f"scraping location data: {query}")
    # the graphql payload that defines our search
    # note: that changing values outside of expected ranges can block the web scraper
    payload = [
            {
                "variables": {
                    "request": {
                        "query": query,
                        "limit": 10,
                        "scope": "WORLDWIDE",
                        "locale": "en-US",
                        "scopeGeoId": 1,
                        "searchCenter": None,
                        # note: here you can expand to search for differents.
                        "types": [
                            "LOCATION",
                            # "QUERY_SUGGESTION",
                            # "RESCUE_RESULT"
                        ],
                        "locationTypes": [
                            "GEO",
                            "AIRPORT",
                            "ACCOMMODATION",
                            "ATTRACTION",
                            "ATTRACTION_PRODUCT",
                            "EATERY",
                            "NEIGHBORHOOD",
                            "AIRLINE",
                            "SHOPPING",
                            "UNIVERSITY",
                            "GENERAL_HOSPITAL",
                            "PORT",
                            "FERRY",
                            "CORPORATION",
                            "VACATION_RENTAL",
                            "SHIP",
                            "CRUISE_LINE",
                            "CAR_RENTAL_OFFICE",
                        ],
                        "userId": None,
                        "context": {},
                        "enabledFeatures": ["articles"],
                        "includeRecent": True,
                    }
                },
                # Every graphql query has a query ID that doesn't change often:
                "query": "84b17ed122fbdbd4",
                "extensions": {"preRegisteredQueryId": "84b17ed122fbdbd4"},
            }
        ]

    # we need to generate a random request ID for this request to succeed
    random_request_id = "".join(
        random.choice(string.ascii_lowercase + string.digits) for i in range(180)
    )
    headers = {
        "X-Requested-By": random_request_id,
        "Referer": "https://www.tripadvisor.com/Hotels",
        "Origin": "https://www.tripadvisor.com",
    }
    result = await client.post(
        url="https://www.tripadvisor.com/data/graphql/ids",
        json=payload,
        headers=headers,
    )
    data = json.loads(result.content)
    results = data[0]["data"]["Typeahead_autocomplete"]["results"]
    results = [r['details'] for r in results if 'details' in r] # strip metadata
    log.info(f"found {len(results)} results")
    return results

# To avoid being instantly blocked we'll be using request headers that
# mimic Chrome browser on Windows
BASE_HEADERS = {
    "authority": "www.tripadvisor.com",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
}
# start HTTP session client with our headers and HTTP2
client = httpx.AsyncClient(
    http2=True,  # http2 connections are significantly less likely to get blocked
    headers=BASE_HEADERS,
    timeout=httpx.Timeout(150.0),
    limits=httpx.Limits(max_connections=5),
)


async def run():
    result = await scrape_location_data("Hue", client)
    print(json.dumps(result, indent=2))
    url = result[0]["ATTRACTIONS_URL"]
    print("url before: ", url)
    index = url.find('Activities-')
    url = url[:index + len('Activities-')] + 'oa0-' + url[index + len('Activities-'):]
    url = 'https://www.tripadvisor.com' + url
    print("url after: ", url)
    # Định nghĩa các thông tin cần gửi trong body của POST request
    payload = {
        "source": "universal",
        "url": url,
        "geo_location": "United States"
    }

    # Đường link gửi request
    url = "https://realtime.oxylabs.io/v1/queries"

    # Định nghĩa thông tin xác thực (Basic Auth)
    credentials = ('minhminh', 'Gogogogo1234')

    # Gửi POST request
    response = requests.post(url, json=payload, auth=credentials)

    # In ra status code của response để kiểm tra
    print("Status code:", response.status_code)

    # In ra nội dung của response
    print("Response content:", response.text)
    content = response.json()["results"][0]["content"]
    print("content:", content)
    soup = BeautifulSoup(content, "html.parser")
    print("soup:", soup)

    data = []
    for div in soup.find_all("div", {"class": "alPVI eNNhq PgLKC tnGGX"}):
        name_div = div.find("div", {"class": "XfVdV"})
        if name_div:
            name = name_div.get_text(strip=True)
            print(name)
        else:
            print("No name found")
            
        rating_tag = div.find('title')
        if rating_tag:
            rating = rating_tag.get_text(strip=True)
        else:
            rating = "No rating found"
        print(rating)

        data.append({
            "name": name,
            "rating": rating
        })

    img_urls = []

    # Sử dụng vòng lặp để tìm tất cả các thẻ <picture> với lớp phù hợp
    for picture in soup.find_all("li", class_="CyFNY _A MBoCH"):
        img_tag = picture.find('img')
        if img_tag:
            img_src = img_tag.get('src')
            img_urls.append(img_src)
            print("Image URL from src attribute:", img_src)

    if len(data) != len(img_urls):
        raise ValueError("Số phần tử trong 'data' và 'img_urls' không khớp")

    for i in range(len(data)):
        data[i]["image"] = img_urls[i]

    df = pd.DataFrame(data)
    df.to_csv("search_results.csv", index=False)

if __name__ == "__main__":
    asyncio.run(run())