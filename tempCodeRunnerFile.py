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

    pattern = r"https?://(?:www\.)?(.*?)\.com"
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
        while len(urls) and count < 15:
            url = urls.popleft()
            scrapped_urls.add(url)

            parts = urllib.parse.urlsplit(url)
            base_url = '{0.scheme}://{0.netloc}'.format(parts)
            path = url[:url.rfind('/')+1] if '/' in parts.path else url
            print('[%d] Processing %s' % (count, url))

            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Raise an HTTPError for bad responses
            except requests.exceptions.RequestException as e:
                print('Error making request:', e)
                continue

            new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
            emails.update(new_emails)
            soup = BeautifulSoup(response.text, features='lxml')

            for anchor in soup.find_all("a"):
                link = anchor.attrs.get('href', '')
                if link.startswith('/'):
                    link = base_url + link
                elif not link.startswith(('http', 'https')):
                    link = path + link
                if link not in urls and link not in scrapped_urls:
                    urls.append(link)

            count += 1

    except KeyboardInterrupt:
        print('[-] Closing')

    filtered_strings = [string for string in emails if extracted_string in string]

    if not filtered_strings:
        filtered_strings = ("No emails found. \n"
                            "1) Website was most likely protected against web crawlers.\n"
                            "2) Recheck the web address you entered.")

    return jsonify(filtered_strings)

if __name__ == "__main__":
    app.run(debug=True)
