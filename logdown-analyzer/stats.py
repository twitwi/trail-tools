
import vuejspython
import numpy as np
import logdown as ld


def pairs_to_dict(l):
    return {k:v for (k,v) in l}

@vuejspython.model
class App:
    path = "example-journal.md"
    entries = []

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
    def aggregate(self, entries):
        return {
            'dist': int(np.sum([e['dist'] for e in entries])),
            'd_pos': int(np.sum([e['d_pos'] for e in entries if e['d_pos'] is not None])),
            'd_neg': int(np.sum([e['d_neg'] for e in entries if e['d_neg'] is not None])),
            'dur': int(np.sum([e['dur'] for e in entries if e['dur'] is not None])),
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

    def computed_weekly_stats_dict(self): return pairs_to_dict(self.weekly_stats)
    def computed_monthly_stats_dict(self): return pairs_to_dict(self.monthly_stats)
        

vuejspython.start(App())


