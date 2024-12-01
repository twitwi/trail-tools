
import sys
import urllib.request
import lxml.etree as ET
import re
from pathlib import Path
import json

def fetch_raw(url):
    req = urllib.request.urlopen(url)
    return req.read()

def fetch_xml(url):
    return ET.fromstring(fetch_raw(url))

def read_info_file(path, keys=[], as_dict=False):
    with open(path) as f:
        o = json.load(f)
    if type(keys) == type("I am a string"):
        return o[keys]
    if as_dict:
        return {k: o[k] for k in keys}
    return [o[k] for k in keys]
    
def load_xml(path):
    return ET.parse(path)


EVENIFDIREXISTS = False
EVENIFFILEEXISTS = False

def go():
    args = sys.argv[1:]
    for a in args:
        if '=' in a:
            n, v = a.split('=', 1)
            globals()[n] = type(globals()[n])(v)

    table_files = [a for a in args if not '=' in a]


    for table_file in table_files:
        m = re.match(r'(.*)-([^-]*)--table.xml', table_file)
        info_file = m.group(1) + '--info.json'
        url = read_info_file(info_file, keys='url')
        subid = m.group(2)
        runners_dir = Path(m.group(1) + '-' + subid + '--runners')

        if not EVENIFDIREXISTS and runners_dir.exists():
            print(runners_dir, 'already exists, skipping (use EVENIFDIREXISTS=1 to force)')
            continue
        runners_dir.mkdir(exist_ok=True)

        xml = load_xml(table_file)
        bibs = xml.xpath('//lignes/l')
        for ibib,bib in enumerate(bibs):
            bnum = bib.attrib['doss']
            if not EVENIFFILEEXISTS and len(list(runners_dir.glob(f'{bnum}--*.xml'))) > 0:
                print('.. bib', bnum, 'already downloaded, skipping (use EVENIFFILEEXISTS=1 to force)')
            else:
                xml = fetch_raw(f'{url}/coureur.php?rech='+bnum)
                itra = '_'.join(ET.fromstring(xml).xpath('//identite/@cid'))
                runner_file = runners_dir / f"{bnum}--{itra}.xml"
                with open(runner_file, 'wb') as f:
                    f.write(xml)
                print('.. bib', bnum, 'saved to', runner_file)

# TODO a get_from_itra (from the ids obtained from all the --runners/... passed as parameters) and a target folder (need to run from time to time to get the history accross time), allow a e.g. GLOB='*--runners/*.xml' to avoid having huge parameters lists
# POST: curl 'https://itra.run/api/Runner/RefreshRunnerPiGeneralStats' -X POST -H 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:104.0) Gecko/20100101 Firefox/104.0' -H 'Accept: */*' -H 'Accept-Language: fr-FR,en-US;q=0.7,en;q=0.3' -H 'Accept-Encoding: gzip, deflate, br' -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -H 'X-Requested-With: XMLHttpRequest' -H 'Origin: https://itra.run' -H 'DNT: 1' --data-raw 'runnerId=754031'

go()








"""
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
"""
