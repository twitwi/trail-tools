
import sys
import lxml.etree as ET
import re
#from collections import namedtuple
from typing import NamedTuple
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def dict_sorted(d):
    r = {}
    for k in sorted(d.keys()):
        r[k] = d[k]
    return r
    
#RacePoint = namedtuple('RacePoint', 'id dist dpos hfirst hlast')
class RacePoint(NamedTuple):
    id: int
    dist: float
    dpos: float
    hfirst: str
    hlast: str
def RacePoint_from_Element(el):
    a = lambda n: el.attrib[n]
    #values = [a(n) for n in 'idpt km d hp hd'.split(' ')]
    #return ANamedTuple(*values)
    return RacePoint(
        int(a('idpt')),
        float(a('km')),
        float(a('d')),
        a('hp'),
        a('hd'),
    )

def minmax(l):
    return (min(l), max(l))
def parcours_hours(s):
    p = s.split('-')
    assert len(p) == 2
    d = int(p[0])
    p = p[1].split(':')
    assert len(p) == 2
    return d*24 + int(p[0]) + int(p[1])/60

def passage_hours(s):
    p = s.split(':')
    assert len(p) == 3
    return int(p[0]) + int(p[1])/60 + int(p[2])/3600
    

class RunSegment(NamedTuple):
    idfrom: int
    idto: int
    dist: float
    dpos: float
    dur: float
    cumul_dist: float
    cumul_dpos: float
    cumul_dur: float
    def cumul_strain(self, dpos_per_km=150):
        return self.cumul_dist + self.cumul_dpos / dpos_per_km
    def strain(self, dpos_per_km=150):
        return self.dist + self.dpos / dpos_per_km
    def hourlystrain(self, dpos_per_km=150):
        return self.strain(dpos_per_km) / self.dur
    
    
def compute_segments(subpoints, bib, RACE_TIME=False):
    segs = []
    prev_id = 0
    base_d = int(subpoints[0].hfirst.split('-')[0])
    delta_d = None
    base_h = prev_h = parcours_hours(subpoints[0].hfirst)
    #base_d = int(re.sub(r'-.*', '', subpoints[0].hfirst))
    #prev_h = base_d * 24 + hours(re.sub(r'.*-', '', subpoints[0].hfirst))
    #print(base_h)
    for pas in bib.xpath('./p'):
        a = lambda n: pas.attrib[n]
        if delta_d is None and a('j') != '': # j="" for DNS
            delta_d = int(a('j')) - base_d
        if a('h') is None or a('h') == '': # drop out
            continue
        cur_id = int(a('idpt'))
        cur_h = (int(a('j')) - delta_d) * 24 + passage_hours(a('h'))
        if cur_id != 0:
            prev_p = subpoints[prev_id]
            cur_p = subpoints[cur_id]
            seg_dur = cur_h - prev_h
            seg_dist = cur_p.dist - prev_p.dist
            seg_dpos = cur_p.dpos - prev_p.dpos
            seg_strain150 = seg_dist + seg_dpos/150
            #print('...', a('idpt'), cur_h, seg_dur, seg_dist, seg_dpos)
            #print('...', a('idpt'), cur_h, seg_strain / seg_dur)
            segs.append(RunSegment(
                prev_id, cur_id,
                seg_dist, seg_dpos, seg_dur,
                cur_p.dist, cur_p.dpos, cur_h - base_h,
            ))
        elif RACE_TIME:
            base_h = cur_h # we have a per-person starting hour
        prev_id = cur_id
        prev_h = cur_h
    return segs
    

def load_xml(path):
    return ET.parse(path)


BOF = '516' # bibs of focus
BOI = '261 463 294 254 75 66' # bibs of interest
RACE_TIME = 1 # set to 0 for hour of passage instead

def go():

    args = sys.argv[1:]
    for a in args:
        if '=' in a:
            n, v = a.split('=', 1)
            globals()[n] = type(globals()[n])(v)

    table_files = [a for a in args if not '=' in a]
    
    per_km = defaultdict(list)
    per_km2 = defaultdict(list)
    per_km3 = defaultdict(list)

    times_at_first = []
    times_at_last = []
    colors = []
    dosss = []

    for table_file in table_files:
        m = re.match(r'(.*)-([^-]*)--table.xml', table_file)
        parcours_file = m.group(1) + '--parcours.xml'
        subid = m.group(2)
    
        pxml = load_xml(parcours_file)
        subpoints = pxml.xpath(f'//points[@course="{subid}"]/pt')
        subpoints = [RacePoint_from_Element(s) for s in subpoints]
        subpoints = {s.id: s for s in subpoints}
        print(subpoints)
        
        xml = load_xml(table_file)
        bibs = xml.xpath('//lignes/l')
        strain_curves = []
        for ibib,bib in enumerate(bibs):
            segs = compute_segments(subpoints, bib, RACE_TIME)
            at = 0 # first ravito, not checking its id actually
            if len(segs) > at:
                times_at_first.append(segs[at].cumul_dur)
                times_at_last.append(segs[-1].cumul_dur)
                colors.append(segs[0].idfrom * 100 + segs[-1].idto)
                dosss.append(bib.attrib['doss'])
            x1s = np.array([s.cumul_dist for s in segs])
            x2s = np.array([s.cumul_strain(150) for s in segs])
            ys = np.array([s.cumul_dur for s in segs])
            more = dict(alpha = 0.03)
            try:
                lstyles = ['solid', 'dashed']
                bnum = bib.attrib['doss']
                if bnum in BOF.split(' '):
                    more = dict(alpha = .9, label=f"/ {bnum}", color="k", ls="dotted")
                elif bnum in BOI.split(' '):
                    more = dict(alpha = .9, label=bnum, ls=lstyles[int(bnum)%2])
            finally: pass
            #plt.plot(x1s, ys, **more)
            plt.plot(x2s, -ys, **more)

    plt.grid()
    plt.legend(loc=0)
    plt.show()

    plt.scatter(times_at_first, times_at_last, 10, c=colors)
    for ibnum,bnum in enumerate(BOF.split(' ')+BOI.split(' ')):
        try:
            i = dosss.index(bnum)
            plt.scatter(times_at_first[i], times_at_last[i], marker="x", label=bnum)
            if ibnum < len(BOF.split(' ')):
                plt.plot(minmax(times_at_first), [times_at_last[i]]*2, c="k", lw=.5)
                plt.plot([times_at_first[i]]*2, minmax(times_at_last), c="k", lw=.5)
        except:
            print(f'bib {bnum} not found')
    plt.xlabel("T Ravito 1")
    plt.ylabel("T Final")
    plt.legend()
    plt.show()

    

go()
