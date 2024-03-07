from bs4 import BeautifulSoup
import requests 
import requests.exceptions
import urllib.parse
from collections import deque
from flask import Flask, jsonify, request
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def basic():
    return 'testing endpoint'

@app.route("/email", methods=['POST'])
def scrape_emails():
    data = request.json.get('data')
    user_url = (data)

    scrapped_urls=set()
    emails=set()
    urls=deque([user_url])

    count=0
    while count<25:
        count+=1

        # store the newest stored url from bs4(check line 46)
        url= urls.popleft()
        
        # adds the url into the set of scrapped url
        scrapped_urls.add(url)
        
        # used urllib module to parse url, used urlsplit to split url into components, why break into components? to contruct a main home page url  
        parts=urllib.parse.urlsplit(url)
        
        # used format method to construct a base url
        base_url='{0.scheme}://{0.netloc}'.format(parts)
        pattern_for_domain = r"https?://(?:www\.)?(.*?)\.com"
        domain = re.search(pattern_for_domain, user_url)
        extracted_domain = domain.group(1)
        path=url[:url.rfind('/')+1] if '/' in parts.path else url
        
        try:
        # Added to mimic request as a mozilla browser
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers)
        # Handles bad requests and moves on towards next url
        except requests.exceptions.RequestException as e:
            continue
        # Checks for emails found from the response.text(converts the url page content into text)
        new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0\-+_]+\.[a-z]+", response.text, re.I))
        emails.update(new_emails)
        # parses through the response for all anchor tags to get more urls
        soup=BeautifulSoup(response.text, features="lxml")
        for anchor in soup.find_all("a"):
            link=anchor.attrs['href'] if 'href' in anchor.attrs else '' 
            if link.startswith('/'):
                link=base_url+ link
            if not link in urls and not link in scrapped_urls:
                urls.append(link)
        
    filtered_emails = [emaail for emaail in emails if extracted_domain in emaail]

    if not filtered_emails:
        filtered_emails = ("No emails found. \n"
                                "1) Website was most likely protected against web crawlers.\n"
                                "2) Recheck the web address you entered.")


    return jsonify(filtered_emails)

if __name__ == "__main__":
    app.run(debug=True)
