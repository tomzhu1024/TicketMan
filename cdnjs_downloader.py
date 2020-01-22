import os

import requests


def download(url, filename):
    r = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(r.content)


urls = """https://cdnjs.cloudflare.com/ajax/libs/highcharts/7.2.0/highcharts.js"""

if __name__ == '__main__':
    for line in urls.split('\n'):
        if line:
            dirs = "/".join(line.split('/')[5:-1])
            if not os.path.exists(dirs):
                print("Dirs created")
                os.makedirs(dirs)
            print("Downloading %s..." % line)
            download(line, line.replace("https://cdnjs.cloudflare.com/ajax/libs/", ""))
            print("Complete!")
