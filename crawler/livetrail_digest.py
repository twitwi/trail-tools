
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
    def strain(self, dpos_per_km=150):
        return self.dist + self.dpos / dpos_per_km
    def hourlystrain(self, dpos_per_km=150):
        return self.strain(dpos_per_km) / self.dur
    
    
def compute_segments(subpoints, bib):
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
        prev_id = cur_id
        prev_h = cur_h
    return segs
    

def load_xml(path):
    return ET.parse(path)


def go():
    table_files = sys.argv[1:]

    per_km = defaultdict(list)
    per_km2 = defaultdict(list)
    per_km3 = defaultdict(list)

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
            segs = compute_segments(subpoints, bib)
            xs = np.array([s.cumul_dist for s in segs])
            hs = np.array([s.hourlystrain(100) for s in segs])
            hs2 = np.array([s.hourlystrain(150) for s in segs])
            hs3 = np.array([s.hourlystrain(200) for s in segs])
            #hs2 = hs2 / hs2[hs>1].mean()
            #hs3 = hs3 / hs3[hs>1].mean()
            #hs = hs / hs[hs>1].mean()
            alpha = 0.03
            try:
                if bib.attrib['doss'] in '516 261 463 75 66 294'.split(' '):
                    alpha = .9
            finally: pass
            plt.plot(xs[hs>0.1], hs[hs>0.1], alpha=alpha)
            #plt.plot(xs[hs>0.1], 1+hs2[hs>0.1], alpha=0.1)
            #plt.plot(xs[hs>0.1], 2+hs3[hs>0.1], alpha=0.1)
            #strain_curves.append(hs)
            for x, h in zip(xs, hs):
                per_km[x].append(h)
            for x, h in zip(xs, hs2):
                per_km2[x].append(h)
            for x, h in zip(xs, hs3):
                per_km3[x].append(h)

    for k in per_km.keys():
        per_km[k] = np.var(per_km[k])*10
    for k in per_km2.keys():
        per_km2[k] = np.var(per_km2[k])*10
    for k in per_km3.keys():
        per_km3[k] = np.var(per_km3[k])*10

    per_km = dict_sorted(per_km)
    per_km2 = dict_sorted(per_km2)
    per_km3 = dict_sorted(per_km3)
    plt.plot(per_km.keys(), np.array(list(per_km.values())))
    plt.plot(per_km2.keys(), np.array(list(per_km2.values())), '--')
    plt.plot(per_km3.keys(), np.array(list(per_km3.values())), '-.')
    
    plt.grid()
    plt.show()

go()
