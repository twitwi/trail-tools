
import sys
import urllib.request
import lxml.etree as ET
import re
import json
import click
from pathlib import Path

def fetch_raw(url):
    req = urllib.request.urlopen(url)
    return req.read()

def fetch_xml(url):
    return ET.fromstring(fetch_raw(url))

def get_events():
    with open(f'config-event-list.txt', 'r') as f:
        events = f.readlines()
        events = [e[:-1] for e in events]
    return events

def get_instances():
    fname = 'config-raw-event-list-from-livetrail.json'
    # load the json file and get the calPass key
    # then each key is an event name, inside there is a res key with inside keys that are years (instances) with a "lien" key
    # return [event, year, lien]
    with open(fname) as f:
        data = json.load(f)['calPass']
        instances = []
        for ename in data:
            event = data[ename]['res']
            for year in event:
                instances.append([ename, year, event[year]['lien']])
    return instances

@click.group()
@click.option('--verbose/--no-verbose', default=False)
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose

@cli.command()
@click.option('--line/--no-line', default=False)
@click.pass_context
def show_events(ctx, line):
    #click.echo(f"Debug is {'on' if ctx.obj['DEBUG'] else 'off'}")
    if line:
        print('\n'.join(get_events()))
    else:
        print(json.dumps(get_events()))

@cli.command()
@click.argument('event')
def getch_event_instances(event):
    fname = f'data/livetrail-{event}--instances.json'
    if Path(fname).exists():
        print(f'{fname} already exists, skipping')
        print(json.load(open(fname)))

    print(f'Getting instances for {event}')
    home = fetch_xml(f'https://{event}.livetrail.net/')
    res = home.xpath('//e[@titre="Historique"]//a/@href')
    with open(fname, 'w') as f:
        json.dump(res, f)
    print(res)

@cli.command()
@click.option('--line/--no-line', default=False)
def show_instances(line):
    if line:
        print('\n'.join([' '.join(i) for i in get_instances()]))
    else:
        print(json.dumps(get_instances(), indent=1))

@cli.command()
def fetch_all_events():
    instances = get_instances()
    for event, year, url in instances:
        if not url.startswith('http'):
            url = f'https://{url}/'

        if not url.endswith('/'):
            url += '/'

        fparcours = f'data/livetrail--{event}--{year}---parcours.xml'
        if Path(fparcours).exists():
            continue
        print(f'## Get {event} {year}')
        with open(fparcours, 'wb') as f:
            parcours = fetch_raw(f'{url}/parcours.php')
            f.write(parcours)
        home = fetch_xml(url)
        subcourse_ids = home.xpath('/d/e/@id')
        with open(f'data/livetrail--{event}--{year}---info.json', 'w') as f:
            info = {
                "url": url,
            }
            json.dump(info, f)
        for scid in subcourse_ids:
            print(f'### Get {event}-{year}-{scid}')
            with open(f'data/livetrail--{event}--{year}--{scid}---table.xml', 'wb') as f:
                ctable = fetch_raw(f'{url}/passages.php?course={scid}&cat=scratch&from=1&to=10000')
                f.write(ctable)
            with open(f'data/livetrail--{event}--{year}--{scid}---stats.xml', 'wb') as f:
                cstats = fetch_raw(f'{url}/stats.php?course={scid}')
                f.write(cstats)

if __name__ == '__main__':
    cli(obj={})

exit()

course_url = sys.argv[1]
if not course_url.startswith('http'):
    course_url = f'https://{course_url}.livetrail.net/'

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
