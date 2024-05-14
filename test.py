from bs4 import BeautifulSoup
import pandas as pd
import requests

# Định nghĩa các thông tin cần gửi trong body của POST request
payload = {
    "source": "universal",
    "url": "https://www.tripadvisor.com/Attractions-g186216-Activities-oa0-United_Kingdom.html",
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


