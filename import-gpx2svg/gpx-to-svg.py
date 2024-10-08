

import gpxpy
import gpxpy.gpx
import sys
import numpy as np

import tools
from tools import latlon_to_tile, tile_to_latlon, get_tile_if_not_present
from jinja2 import Template
from itertools import groupby

def log(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

template = Template("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns="http://www.w3.org/2000/svg"
   width="297mm"
   height="210mm"
   viewBox="{{viewbox}}"
   id="svg2"
   version="1.1"
>
  <g
     id="layer1"
     transform="translate(0, 0)" >
    <g style="image-rendering:optimizeSpeed">
      {% for t in tiles %}
      <image transform="translate({{t[1]-lonoff}}, {{t[0]-latoff}}) scale({{1/256}})"
             width="256" height="256" xlink:href="{{t[-1]}}"/>
      {% endfor %}
    </g>
    <path d="{{gpxtrack}}" style="stroke-width: {{5*unit}}; stroke: red; fill:none;  stroke-dasharray: {{10*unit}},{{10*unit}}" />
    <path d="{{gpxhull}}" style="stroke-width: {{unit}}; stroke: blue; fill: black; opacity: 0.5" />
    <g fill="#F00" >
        {% for p in roadpoints %}
        <circle cx="{{p[1]-lonoff}}" cy="{{p[0]-latoff}}" r="{{3*unit}}" />
        {% endfor %}
    </g>
    <g fill="#3A3" >
        {% for p in pathpoints %}
        <circle cx="{{p[1]-lonoff}}" cy="{{p[0]-latoff}}" r="{{3*unit}}" />
        {% endfor %}
    </g>
    <g>
      {% for m in latmarks %}
      <g transform="translate({{m[1]-lonoff}}, {{m[0]-latoff}})" >
        <line x1="-{{m[4]}}" x2="{{m[4]}}" style="stroke: #000; stroke-width: {{m[3]*unit}}; stroke-dasharray: {{m[3]*unit}},{{m[3]*unit}}"/>
        <text x="{{m[4]*1.05}}" y="{{m[3]*4*unit}}" style="font-size: {{m[3]*10*unit}}; fill: black;">{{m[2]}}</text>
      </g>
      {% endfor %}
    </g>
  </g>
</svg>
""")

tileset = 'osm' #'hikebike' #'topo'
tools.TILE_FORMAT = "./tiles/tile-{}-{}-{}-{}.png"
z = 15

map_horizon = 0.005 # None
gpx_file = open(sys.argv[1], 'r')
gpx = gpxpy.parse(gpx_file)
STEP = 1 # 10, set to 1 if it comes from graphhopper etc
# TODO use file size to guess the 1 or 10
HULL_STEP = 5 # 5
HULL_WIDTH = .2#0.03

needed_tiles = set()

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points[::STEP]:
            #log('Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation))
            #log(latlon_to_tile((point.latitude, point.longitude), z))
            plat = point.latitude
            plon = point.longitude
            needed_tiles.add(latlon_to_tile((plat, plon), z, as_int=True))
            if map_horizon is not None:
                h = map_horizon
                needed_tiles.add(latlon_to_tile((plat-h, plon-h), z, as_int=True))
                needed_tiles.add(latlon_to_tile((plat-h, plon+h), z, as_int=True))
                needed_tiles.add(latlon_to_tile((plat+h, plon-h), z, as_int=True))
                needed_tiles.add(latlon_to_tile((plat+h, plon+h), z, as_int=True))

def ipoints(gp, z=z):
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points[::STEP]:
                ij = latlon_to_tile((point.latitude, point.longitude), z)
                yield (*reversed(ij), point.latitude, point.longitude)

def enrich_tile(t):
    # global z
    fname = get_tile_if_not_present(tileset, *t, z)
    low = tile_to_latlon(t, z)
    high = tile_to_latlon(t, z, add_one=True)
    return (*reversed(t), *low, *high, z, fname)

ILAT, ILON, LATMIN, LONMIN, LATMAX, LONMAX, Z  = range(7)
tiles = list(map(enrich_tile, needed_tiles))

data = np.array(tiles)[:,:-1].astype(np.float64)
vbminilat = data[:,ILAT].min()
vbmaxilat = data[:,ILAT].max()+1
vbminilon = data[:,ILON].min()
vbmaxilon = data[:,ILON].max()+1
vbminlat = data[:,LATMIN].min()
vbmaxlat = data[:,LATMAX].max()
vbminlon = data[:,LONMIN].min()
vbmaxlon = data[:,LONMAX].max()

def mround(v, step):
    return int((v+step/2)/step) * step

latoff = vbminilat
lonoff = vbminilon
#viewbox = "{} {} {} {}".format(vbminlon, vbminlat, vbmaxlon-vbminlon, vbmaxlat-vbminlat)
viewbox = "{} {} {} {}".format(0, 0, vbmaxilon-vbminilon, vbmaxilat-vbminilat)
def svg_path(apoints):
    def pos(p):
        return "{} {}".format(p[1]-lonoff, p[0]-latoff)
    return "M " + " L ".join([pos(p) for p in apoints])

def dhull(apoints, STEP = HULL_STEP):
    def add_right(b, a, l = HULL_WIDTH):
        d = ((b[0]-a[0])**2 + (b[1]-a[1])**2)**0.5
        if d==0:
            log("ZZEEEEEEEEEEEEEEEEEEEEEEEEERRRRRRRRRRRRRRRRRROOOOOOOOOOOOOO")
            d = 1
            #exit()
        return (b[0] + (b[1]-a[1]) * l / d, b[1] - (b[0]-a[0]) * l / d)
    ps = apoints[::STEP] + apoints[::-STEP]
    return [ps[0]] + [add_right(ps[i], ps[i-1]) for i in range(1, len(ps)) ] + [ps[0]]

def latmarks(apoints):
    res = []
    def addby(step, swidth, shalflen=1, forcetxt=None):
        vals = [ (ilat, ilon, "{:3.4f}".format(mround(lat, step))) for ilat, ilon, lat, _ in apoints ]
        def third(o): return o[2]
        vals = sorted(vals, key=third)
        for k, g in groupby(vals, third):
            data = np.array(list(g), dtype=np.float64)
            txt = k if forcetxt is None else forcetxt
            imed = np.median(data[:,:2], axis=0) # ilat,ilon
            med = tile_to_latlon((imed[1], imed[0]), z) # lat,lon
            _, ilat = latlon_to_tile((float(k), med[1]), z)
            res.append( (ilat, imed[1], txt, swidth, shalflen) )
    #addby(0.0002, 1)
    addby(0.005, 2, shalflen=1.8)
    #addby(0.001, 1, forcetxt="", shalflen=0.5)
    return res

Qformat_path = """way[highway~"track|path"](poly:"{}");>;out;"""
Qformat_road = """way[!building][highway][highway!~"track|path"][!amenity](poly:"{}");>;out;"""
def lazy_overpass(gpshull, Qformat, cache_file = ",,cache-overpass"):
    import pickle
    import os
    if os.path.isfile(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    else:
        import overpass
        def pos(p):
            return "{} {}".format(p[0], p[1])
        poly = " ".join([ pos(p) for p in gpshull ])
        log("Querying overpass, please wait... ({})".format(cache_file))
        data = overpass.API().Get(Qformat.format(poly))
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        return data

def all_overpass(apoints, base_cache = ",,cache-overpass", OVERCHUNK = 100, z=z):
    roads = []
    paths = []
    log("Will stop at", len(apoints)-1)
    for istart in range(0, len(apoints)-1, OVERCHUNK):
        hull = dhull(apoints[istart:istart+OVERCHUNK])
        gpshull = [tile_to_latlon((p[1], p[0]), z) for p in hull]
        ov = lazy_overpass(gpshull, Qformat_road, base_cache+'-'+str(OVERCHUNK)+'-'+str(istart)+'-road')
        roads += ov.features
        ov = lazy_overpass(gpshull, Qformat_path, base_cache+'-'+str(OVERCHUNK)+'-'+str(istart)+'-path')
        paths += ov.features
    return roads, paths

def partition_path(apoints, osmpoints):
    from scipy import spatial
    res = [ [] for _ in osmpoints ]
    trees = [
              spatial.cKDTree([[p.geometry.coordinates[1], p.geometry.coordinates[0]] for p in pointset])
              for pointset in osmpoints ]
    for p in apoints:
        coo = [p[2], p[3]]
        dists = [ t.query([coo])[0] for t in trees ]
        res[np.argmin(dists)].append(p)
    return res

apoints = list(ipoints(gpx))
#apoints_by_types = [[],[]]
osmpoints = all_overpass(apoints)
apoints_by_types = partition_path(apoints, osmpoints)
log(*map(len, osmpoints))

print(template.render(tiles=tiles, z=z, viewbox=viewbox, gpxtrack=svg_path(apoints),
                      gpxhull=svg_path(dhull(apoints)), latmarks=latmarks(apoints),
                      roadpoints=apoints_by_types[0], pathpoints=apoints_by_types[1],
                      unit=2**(z-14)/256, latoff=latoff, lonoff=lonoff))
