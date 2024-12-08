
import sys
import urllib.request
import lxml.etree as ET
import re
import json
import click
from pathlib import Path
from glob import glob as globglob

config = dict(
    raw_event_list='config-raw-event-list-from-livetrail.json',
    #data/livetrail--ut4m--2023--160C---table.xml
    races_glob='data/livetrail--*--table.xml',
    races_glob_regexp=r'data/livetrail--([^-].*)--([^-].*)--([^-].*)---table.xml',
)

def fetch_raw(url):
    req = urllib.request.urlopen(url)
    return req.read()

def fetch_raw_with_cookie(url, cname, cval):
    req = urllib.request.Request(url)
    req.add_header('Cookie', f'{cname}={cval}')
    req = urllib.request.urlopen(req)
    return req.read()

def as_xml(str):
    return ET.fromstring(str)

def fetch_xml(url):
    return as_xml(fetch_raw(url))

def load_xml(f):
    return ET.parse(f)


def get_events(fname=None):
    if fname is None:
        fname = config['raw_event_list']
    with open(fname) as f:
        data = json.load(f)['calPass']
        return list(data.keys())

def get_instances(fname=None):
    if fname is None:
        fname = config['raw_event_list']
    with open(fname) as f:
        data = json.load(f)['calPass']
        instances = []
        for ename in data:
            event = data[ename]['res']
            for year in event:
                instances.append([ename, year, event[year]['lien']])
    return instances

def get_races(glob=None, regexp=None):
    if glob is None:
        glob = config['races_glob']
    if regexp is None:
        regexp = config['races_glob_regexp']
    res = []
    for f in globglob(glob):
        g = re.match(regexp, f)
        res.append(g.groups())
    return res

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

#@cli.command()
#@click.argument('event')
#def getch_event_instances(event):
#    fname = f'data/livetrail-{event}--instances.json'
#    if Path(fname).exists():
#        print(f'{fname} already exists, skipping')
#        print(json.load(open(fname)))
#
#    print(f'Getting instances for {event}')
#    home = fetch_xml(f'https://{event}.livetrail.net/')
#    res = home.xpath('//e[@titre="Historique"]//a/@href')
#    with open(fname, 'w') as f:
#        json.dump(res, f)
#    print(res)

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
        froot = f'data/livetrail--{event}--{year}---root.xml'
        if Path(froot).exists():
            continue
        if Path(fparcours).exists():
            continue
        print(f'## Get {event} {year}')
        with open(froot, 'wb') as f:
            _root = fetch_raw(url)
            f.write(_root)
            home = ET.fromstring(_root)
        with open(fparcours, 'wb') as f:
            parcours = fetch_raw(f'{url}/parcours.php')
            f.write(parcours)
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
            # NB: could have got these all in one with course=T but whatever
            with open(f'data/livetrail--{event}--{year}--{scid}---stats.xml', 'wb') as f:
                cstats = fetch_raw(f'{url}/stats.php?course={scid}')
                f.write(cstats)

@cli.command()
def fetch_all_race_runners():
    races = get_races()
    for event, year, rname in races:

        details = ''
        ### CUSTOM FILTER
        if int(year) < 2022: continue
        with open(f'data/livetrail--{event}--{year}---parcours.xml', 'rb') as f:
            parcours = load_xml(f)
            last = parcours.xpath(f'//points[@course="{rname}"]/pt[last()]')
            if len(last) == 0:
                print(f'## {event} {year} {rname} has no last point')
                continue
            dist = float(last[0].attrib['km'])
            if dist < 60: continue
            details += f' | {dist}km'
        ### /

        out = f'data/livetrail--{event}--{year}--{rname}---runners.xml'
        if Path(out).exists():
            continue
        print(f'## {event} {year} {rname}{details}')
        with open(out, 'wb') as f:
            pass
        fname = f'data/livetrail--{event}--{year}--{rname}---table.xml'
        if not Path(fname).exists():
            continue
        with open(f'data/livetrail--{event}--{year}---info.json') as f:
            info = json.load(f)
            url = info['url']
        data = load_xml(fname)
        bibs = data.xpath('//lignes/l/@doss')
        all = None
        # get them 15 by 15
        for i in range(0, len(bibs), 15):
            print(f'### {i}..{i+15}')
            bibs15 = bibs[i:i+15]
            cookie = '%2C'.join(str(bib) for bib in bibs15)
            #fetch url with cookie comp
            xml = as_xml(fetch_raw_with_cookie(f'{url}/compare.php', 'comp', cookie))
            for fiche in xml.xpath('/d/fiche'):
                for child in fiche:
                    if child.tag == 'palm':
                        for subchild in child:
                            child.remove(subchild)
                    elif child.tag == 'identite':
                        pass
                    else:
                        fiche.remove(child)
            if all is None:
                all = xml
            else:
                for fiche in xml.xpath('/d/fiche'):
                    all.append(fiche)
        with open(out, 'wb') as f:
            f.write(ET.tostring(all))
                
                

@cli.command()
def compile_race_infos():
    races = get_races()
    for event, year, rname in races:
        #print(f'## {event} {year} {rname}')
        fname = f'data/livetrail--{event}--{year}--{rname}---stats.xml'
        if not Path().exists() or Path(fname).stat().st_size < 180:
            continue
        with open(fname, 'rb') as f:
            data = load_xml(f)
            started = int(data.xpath('//stat/@nbp')[0])
            dropped = int(data.xpath('//stat/@nba')[0])
            print(100000*dropped/(1e-100+started), started, event, year, rname)
    #print(json.dumps(races, indent=1))
    #for fname in globglob(glob):
    #    if Path(fname).stat().st_size == 0:
    #        continue
    #    print(f'## {fname}')
    #    data = load_xml(fname)
    #    print(data)

if __name__ == '__main__':
    cli(obj={})
