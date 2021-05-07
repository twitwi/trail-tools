
import vuejspython
import glob
#import numpy as np
#import subprocess
from pathlib import Path
#import random
#import asyncio
import gpx_parser
import json


def pairs_to_dict(l):
    return {k:v for (k,v) in l}

#def max0(a):
#    if len(a) == 0: return 0
#    else: return np.max(a)

@vuejspython.model
class Segments:
    # path = "example-journal.md"
    gpx_cwd = str(Path.home())+"/doc/notes/gpx"
    # entries = []
    # currentlyRunning = []
    all_gpx = []
    cache_path = ".cache.json"

    i = 3
    def incr(self, d):
        self.i += d


    def __init__(self):
        pass
        #self.watch_path(self.path)
        self.gpxbounds_cache = {}
        self.gpxbounds_cache_needs_saving = False
        self.load_gpxbounds_cache()
    
    async def doCall(self, what, e, cwd, *cmd):
        if e is None:
            e = {'date': 'global'}
        r = {
            'id': what+'--'+e['date']+'--'+str(random.random()),
            'text': what+'('+e['date']+')',
        }
        self.currentlyRunning.append(r)
        proc = await asyncio.create_subprocess_shell(' '.join(cmd))
        await asyncio.wait_for(proc.wait(), timeout=None)
        self.currentlyRunning.remove(r)

    def listAllGpx(self):
        self.all_gpx = sorted(glob.glob(self.gpx_cwd + '/*.gpx'))

    def maybe_save_gpxbounds_cache(self):
        if not self.gpxbounds_cache_needs_saving: return
        with open(self.cache_path, 'w') as f:
            json.dump(self.gpxbounds_cache, f, sort_keys=True, indent=2)

    def load_gpxbounds_cache(self):
        try:
            with open(self.cache_path, 'r') as f:
                self.gpxbounds_cache = json.load(f)
        except FileNotFoundError as e:
            pass # just no cache

    def getGpxBounds(self, p):
        if p in self.gpxbounds_cache:
            return self.gpxbounds_cache[p]
        res = 0,0,0,0
        try:
            with open(p, 'r') as gpx_file:
                gpx = gpx_parser.parse(gpx_file)
                res = gpx.get_bounds()
        except BaseException as e:
            print("Failed with", p, e)
        self.gpxbounds_cache[p] = res
        self.gpxbounds_cache_needs_saving = True
        return res

    def listGpxInBox(self, bounds, ifrom=None, iend=None):
        latm = bounds['_southWest']['lat']
        latM = bounds['_northEast']['lat']
        lngm = bounds['_southWest']['lng']
        lngM = bounds['_northEast']['lng']
        res = []
        for p in sorted(glob.glob(self.gpx_cwd + '/*.gpx'))[slice(ifrom, iend)]:
            print(p)
            glatm, glatM, glngm, glngM = self.getGpxBounds(p)
            # surely out of the box
            if glatM < latm or glatm > latM or glngM < lngm or glngm > lngM:
                continue
            # surely in the box
            if latm < glatm < glatM < latM and lngm < glngm < glngM < lngM:
                res.append(p)
                continue
            # need fine evaluation
            try:
                with open(p, 'r') as gpx_file:
                    gpx = gpx_parser.parse(gpx_file)
                for (point, t, s, i) in gpx.walk():
                    if latm < point.latitude < latM and lngm < point.longitude < lngM:
                        res.append(p)
                        break
            except BaseException as e:
                print("Failed with", p, e)
        self.maybe_save_gpxbounds_cache()
        self.all_gpx = res

    def readGpxFile(self, p):
        with open (p, "r") as f:
            data = f.read()
        return data

    def runShellCommand(self, what, e):
        cwd = self.gpx_cwd
        go = lambda *cmd: asyncio.ensure_future(self.doCall(what, e, cwd, 'cd', cwd, '&&', *cmd))
        if what == 'generic':
            go('./generic.sh', str(e['date'])+'*.gpx', 'vel=ddist', 'shouldwait=false')
        elif what == 'smooth':
            go('python3', '$HOME/projects/trail-tools/to-import/gpxlib.py', str(e['date'])+'*.gpx', 'old', 'fast')
        elif what == 'gpxsee':
            go('gpxsee', str(e['date'])+'*.gpx')
        elif what == 'edit-logs':
            go('emacs', self.path)
        elif what == 'edit-parcourstest':
            go('libreoffice', '$HOME/projects/nextcloud-mycorecnrs/random/TrainimmXT.xlsx')
        elif what == 'edit-notes':
            import re
            go('emacs', re.sub(r'[.]md$', r'-notes.md', self.path))




