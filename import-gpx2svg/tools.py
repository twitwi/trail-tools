

import configparser as cparser
import sys
from io import StringIO
import re
import json
from scipy import misc
import numpy as np
import os
from os import path


used_keys = []    
def read_cfg(cfg_filename, more_lines=None):
    if more_lines is None: # default value for more_lines: look into the env
        if 'MORE' in os.environ:
            more_lines = os.environ['MORE'].split(".|.")
        else:
            more_lines = []
    cfg_str = '[default]\n'
    with open (cfg_filename, 'r') as myfile:
        cfg_str += myfile.read()
    for l in more_lines:
        cfg_str += '\n' + l
    #cfg_str = re.sub(r'(\n[^=]*)=', r'\1:', cfg_str)
    cfg = cparser.ConfigParser()
    cfg.readfp(StringIO(cfg_str))
    return cfg

def read_pair(cfg, key):
    sec = cfg.sections()[0]
    used_keys.append(key)
    v = cfg.get(sec, key)
    v1, v2 = v.split(',')
    return (float(v1),float(v2))

def read_json(cfg, key, default):
    sec = cfg.sections()[0]
    try:
        used_keys.append(key)
        v = cfg.get(sec, key)
    except:
        return default
    return json.loads(v)

def read_default(cfg, key, default):
    sec = cfg.sections()[0]
    try:
        used_keys.append(key)
        return cfg.get(sec, key)
    except:
        return default

def minmax_pairs(a, b):
    m0 = min(a[0], b[0])
    m1 = min(a[1], b[1])
    return (m0, m1) , (a[0]+b[0]-m0, a[1]+b[1]-m1)

def latlon_to_tile(lat__lon,z, as_int=False):
    lat,lon = lat__lon
    from numpy import log, tan, cos, pi, radians
    x = (lon + 180.0) / 360.0 * (1<<z)
    y = (1 - log(tan(radians(lat)) + 1 / cos(radians(lat))) / pi) / 2.0 * (1<<z)
    if as_int:
        return int(x),int(y)
    else:
        return x,y

def tile_to_latlon(x__y, z, add_one=False):
    x,y = x__y
    if add_one:
        x += 1
        y += 1
    from numpy import sinh, pi, degrees
    from numpy import arctan as atan
    lat = degrees(atan(sinh(pi * (1.0 - 2.0 * y / float(1<<z)))))
    lon = x / float(1<<z) * 360.0 - 180.0
    return lat, lon

def classic(prefix):
    def sub(x,y,z):
        return prefix+"{}/{}/{}.png".format(z,x,y)
    return sub

TILE_FORMAT = "../tiles/tile-{}-{}-{}-{}.png"
def tile_file(name, x,y,z):
    return TILE_FORMAT.format(name, z,x,y)

tile_sets = {
    "osm": classic("http://tile.openstreetmap.org/"),
    "topo": classic("https://c.tile.opentopomap.org/"),
    #"esritopo": classic("https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/"),
    "transport": classic("http://c.tile.thunderforest.com/transport/")
}

def get_tile_if_not_present(tileset, x,y,z, verbose=True):
    fname = tile_file(tileset, x,y,z)
    if not path.isfile(fname):
        url = tile_sets[tileset](x,y,z)
        if verbose:
            print("wget {}".format(url), file=sys.stderr)
        run_cmd("wget", url, "--quiet", "-O", fname)
    return fname


def swap(a__b):
    a,b = a__b
    return b,a

def get_config(cfg_filename='config.cfg', correct_projection=False, **kwargs):
    cfg = read_cfg(cfg_filename, **kwargs)
    # area
    landmark = read_pair(cfg, 'destination')
    mmin, mmax = minmax_pairs(read_pair(cfg, 'from'), read_pair(cfg, 'to'))
    z = read_json(cfg, 'z', None)
    assert not z is None
    if correct_projection:
        mmin = swap(latlon_to_tile(mmin, z))
        mmax = swap(latlon_to_tile(mmax, z))
    # 
    composite_args = read_default(cfg, 'composite_args', '.9,.1,.1,-.1')
    # view
    output_filename = read_default(cfg, 'output', 'color.png')
    extent = [mmin[0], mmax[0], mmin[1], mmax[1]]
    extentT = [mmin[1], mmax[1], mmin[0], mmax[0]] # transposed
    no_colormap = read_json(cfg, 'no-colormap', None)
    no_levellines = read_json(cfg, 'no-levellines', None)
    no_levellinelabels = read_json(cfg, 'no-levellinelabels', None)
    griddata = read_default(cfg, 'griddata', 'linear')
    griddata_smoothsigma = read_json(cfg, 'griddata_smoothsigma', 0.0)
    G = int(read_default(cfg, 'G', '300'))
    cmapname = read_default(cfg, 'cmapname', 'simple1')
    cmapalpha = read_json(cfg, 'cmapalpha', 1.0)
    bgname = read_default(cfg, 'bgname', ',,crop.png')
    mask = read_default(cfg, 'mask', None)
    mask_color = read_json(cfg, 'mask_color', [255, 255, 255])
    mask_color_is_content = read_json(cfg, 'mask_color_is_content', True)
    mask_erode_dilate = read_json(cfg, 'mask_erode_dilate', [])
    bg_tiles = read_default(cfg, 'bg_tiles', "osm")
    try:
        bg = misc.imread(bgname)
        w_px = bg.shape[1]
        h_px = bg.shape[0]
    except:
        print("Exception while opening background file: "+str(bgname))
        print("Continuing anyway")
    bin_x = (mmax[0] - mmin[0]) / G
    bin_y = (mmax[1] - mmin[1]) / G
    levels = read_json(cfg, 'levels', None)
    levelline_color = read_json(cfg, 'levelline_color', ['k', 'darkred', 'r'])
    levelline_width = read_json(cfg, 'levelline_width', 2.0)
    levelline_fontsize = read_json(cfg, 'levelline_fontsize', 15.0)
    rescale_z = read_json(cfg, 'rescale_z', None)
    max_z = read_json(cfg, 'max_z', None)
    kml = read_default(cfg, 'kml', "")
    return obj_dic(locals())

# convert a dict to an object (single level)
def obj_dic(d):
    top = type('new', (object,), d)
    seqs = tuple, list, set, frozenset
    for i, j in d.items():
        setattr(top, i, j)
    return top

import subprocess
def run_cmd(*args):
    return subprocess.call(args)


import os
if 'HELP' in os.environ:
    import re
    conf = get_config()
    print(sorted(used_keys))
    mark = "\033[3;93m!\033[0;m"
    for k in [_ for _ in sorted(get_config().__dict__.keys()) if not _.startswith('__')]:
        val = str(conf.__dict__[k])
        val = re.sub(r"\n(.|\n)*", " ... (more lines)", val)
        c = 94
        possible_mark = '' if k in used_keys else mark
        print("{}\033[3;{}m {} \033[0;m: {}".format(possible_mark, c, k, val))
    c = 91
    print("{}\033[3;{}mWarning\033[0;m: the variables names (shown above) might differ from the config keys (shown at the beginning)".format(mark, c))
    sys.exit()
