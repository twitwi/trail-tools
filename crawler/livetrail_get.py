
import sys
import urllib.request
import lxml.etree as ET
import re
import json

def fetch_raw(url):
    req = urllib.request.urlopen(url)
    return req.read()

def fetch_xml(url):
    return ET.fromstring(fetch_raw(url))


course_url = sys.argv[1]
if not course_url.startswith('http'):
    course_url = f'https://{course_url}.livetrail.run/'

if not course_url.endswith('/'):
    course_url += '/'

    
cid = re.sub(r'^[^:]*://', '', course_url)
cid = re.sub(r'[.:/]', '_', cid)
if len(sys.argv) > 2:
    cid = sys.argv[2]

print(f'## Get {cid}')

with open(f'data/livetrail-{cid}--parcours.xml', 'wb') as f:
    parcours = fetch_raw(f'{course_url}/parcours.php')
    f.write(parcours)

home = fetch_xml(course_url)
subcourse_ids = home.xpath('/d/e/@id')

with open(f'data/livetrail-{cid}--info.json', 'w') as f:
    info = {
        "url": course_url,
    }
    json.dump(info, f)


for scid in subcourse_ids:
    print(f'### Get {cid}-{scid}')
    with open(f'data/livetrail-{cid}-{scid}--table.xml', 'wb') as f:
        ctable = fetch_raw(f'{course_url}/passages.php?course={scid}&cat=scratch&from=1&to=10000')
        f.write(ctable)
    with open(f'data/livetrail-{cid}-{scid}--stats.xml', 'wb') as f:
        cstats = fetch_raw(f'{course_url}/stats.php?course={scid}')
        f.write(cstats)


print("## Previous editions")
print(home.xpath('//e[@titre="Historique"]//a/@href'))
