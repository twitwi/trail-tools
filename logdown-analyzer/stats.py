
import vuejspython
import numpy as np
import logdown as ld
import subprocess
from pathlib import Path
import random
import asyncio

import segments

def pairs_to_dict(l):
    return {k:v for (k,v) in l}

def max0(a):
    if len(a) == 0: return 0
    else: return np.max(a)

@vuejspython.model
class App:
    path = "example-journal.md"
    gpx_cwd = str(Path.home())+"/doc/notes/gpx"
    entries = []
    currentlyRunning = []

    def __init__(self):
        self.watch_path(self.path)
    
    def watch_path(self, v):
        self.entries[:] = []
        try:
            self.entries[:] = list(reversed([vars(e) for e in ld.parse_logdown(self.path)]))
        except:
            pass

    def computed_total(self): return self.aggregate(self.entries)

    def computed_total_distance(self): return int(np.sum([e['dist'] for e in self.entries]))
    def computed_total_dplus(self): return int(np.sum([e['d_pos'] for e in self.entries if e['d_pos'] is not None]))
    def computed_total_dminus(self): return int(np.sum([e['d_neg'] for e in self.entries if e['d_neg'] is not None]))
    
    def aggregate(self, entries, agg=np.sum):
        return {
            'dist': int(agg([e['dist'] for e in entries])),
            'd_pos': int(agg([e['d_pos'] for e in entries if e['d_pos'] is not None])),
            'd_neg': int(agg([e['d_neg'] for e in entries if e['d_neg'] is not None])),
            'dur': int(agg([e['dur'] for e in entries if e['dur'] is not None])),
        }

    def computed_weekly_stats(self):
        weeks = list(reversed(sorted(list(set((e['week'] for e in self.entries))))))
        groups = { w: [] for w in weeks }
        for e in self.entries:
            groups[e['week']].append(e)
        res = [(w, self.aggregate(groups[w])) for w in weeks]
        return res

    def computed_monthly_stats(self):
        months = list(reversed(sorted(list(set((e['month'] for e in self.entries))))))
        groups = { m: [] for m in months }
        for e in self.entries:
            groups[e['month']].append(e)
        res = [(m, self.aggregate(groups[m])) for m in months]
        return res

    def computed_yearly_stats(self):
        years = list(sorted(list(set((e['date'][:4] for e in self.entries))), reverse=True))
        groups = { m: [] for m in years }
        for e in self.entries:
            groups[e['date'][:4]].append(e)
        res = [(m, self.aggregate(groups[m])) for m in years]
        return res

    def computed_shoely_stats(self):
        shoes = list(set((e['shoes'] for e in self.entries)))
        groups = { m: [] for m in shoes }
        for e in self.entries:
            groups[e['shoes']].append(e)
        shoes = sorted(shoes, key=lambda s: groups[s][0]['date'], reverse=True)
        res = [(m, self.aggregate(groups[m])) for m in shoes]
        return res

    def computed_weekly_stats_dict(self): return pairs_to_dict(self.weekly_stats)
    def computed_monthly_stats_dict(self): return pairs_to_dict(self.monthly_stats)
    def computed_yearly_stats_dict(self): return pairs_to_dict(self.yearly_stats)
    def computed_shoely_stats_dict(self): return pairs_to_dict(self.shoely_stats)

    def computed_max_daily_stats(self): return self.aggregate(self.entries, agg=max0)
    def computed_max_weekly_stats(self): return self.aggregate([t[1] for t in self.weekly_stats], agg=max0)
    def computed_max_monthly_stats(self): return self.aggregate([t[1] for t in self.monthly_stats], agg=max0)
    def computed_max_yearly_stats(self): return self.aggregate([t[1] for t in self.yearly_stats], agg=max0)
    def computed_max_shoely_stats(self): return self.aggregate([t[1] for t in self.shoely_stats], agg=max0)

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

vuejspython.start(App(), http_port=4299, py_port=42999)

