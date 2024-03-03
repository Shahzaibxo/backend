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

    if "www."  not in user_url:
        user_url = "www." + user_url
    
    if "https://" not in user_url:
        user_url = "https://" + user_url
    
    pattern = r"www\.(.*?)\.com"

    match = re.search(pattern, user_url)

    if match:
        extracted_string = match.group(1)
        print("Extracted String:", extracted_string)
    else:
        print("No match found.")

    urls = deque([user_url])
    scrapped_urls = set()
    emails = set()

    count = 0
    try:
        while len(urls):
            count += 1
            if count == 25:
                break
            url = urls.popleft()
            scrapped_urls.add(url)

            parts = urllib.parse.urlsplit(url)
            base_url = '{0.scheme}://{0.netloc}'.format(parts)

            path = url[:url.rfind('/')+1] if '/' in parts.path else url
            print('[%d] Processing %s' % (count, url))
            try:
                response = requests.get(url)
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                continue
            new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
            emails.update(new_emails)
            soup = BeautifulSoup(response.text, features='lxml')

            for anchor in soup.find_all("a"):
                link = anchor.attrs['href'] if 'href' in anchor.attrs else ''
                if link.startswith('/'):
                    link = base_url + link
                elif not link.startswith('http'):
                    link = path + link
                if not link in urls and not link in scrapped_urls:
                    urls.append(link)
    except KeyboardInterrupt:
        print('[-] Closing')
    filtered_strings = [string for string in emails if extracted_string in string]
    if filtered_strings=="":
        filtered_strings="No emails found. \n 1)Website was most likely protected against webscrawlers.\n 2)Recheck the web-address you entered."
    return jsonify(filtered_strings)

if __name__ == "__main__":
    app.run(debug=True)