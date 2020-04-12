
import vuejspython
import numpy as np
import subprocess
from pathlib import Path
import random
import asyncio

import gpx_parser as parser
from scipy.sparse import dok_matrix


def pairs_to_dict(l):
    return {k:v for (k,v) in l}

def max0(a):
    if len(a) == 0: return 0
    else: return np.max(a)


def add_points_from_all(agg, step, gpx_files):
    for gpx in gpx_files:
        print(gpx)
        add_points(agg, step, gpx)

def add_points(agg, step, gpx_path):
    with open(gpx_path, 'r') as gpx_file:
        gpx = parser.parse(gpx_file)
    prev = None
    for (point, t, s, i) in gpx.walk():
        #if prev is None:
            y = int(point.latitude / step)
            x = int(point.longitude / step)
            agg[y, x] += 1
        #else:
        #    for α in np.linspace(0, 1, 1, endpoint=False):
        #        y = int((α*prev.latitude  + (1-α)*point.latitude ) / step)
        #        x = int((α*prev.longitude + (1-α)*point.longitude) / step)
        #        agg[y, x] += 1
        #prev = point
    #print("{} tracks loaded".format(len(gpx)))
    #for track in gpx:
    #    print('Track with {} segments and {} points'.
    #        format(len(track), track.get_points_no()))
    #    for segment in track:
    #        print('Segment with %s points' % len(segment))
    #        for point in segment:
    #            print(point)

gpx202004 = "2020-04-01_18-12-43.gpx 2020-04-02_17-06-33.gpx 2020-04-03_18-24-53.gpx 2020-04-04_17-54-45.gpx 2020-04-05_14-40-36.gpx 2020-04-06_16-47-31.gpx 2020-04-07_17-31-36.gpx 2020-04-08_18-13-00.gpx 2020-04-09_17-00-11.gpx 2020-04-11_08-17-22.gpx 2020-04-10_08-18-37.gpx".split()
gpx202003corona = "2020-03-24_07-36-50.gpx 2020-03-25_17-04-03.gpx 2020-03-26_16-45-03.gpx 2020-03-27_16-59-29.gpx 2020-03-28_17-20-13.gpx 2020-03-29_15-03-27.gpx 2020-03-30_17-47-48.gpx 2020-03-31_18-32-40.gpx".split()


@vuejspython.model
class App:
    i = 0

    # TODO across time
    unit_m = 1e-5
    l0step = 10 * unit_m
    l0H = int(180/l0step) +1
    l0W = int(2*l0H) +1
    info = []
    all_gpx = gpx202004 + gpx202003corona

    view_x = 0
    view_y = 0
    view_w = 300
    view_h = 200

    def index(self, pos):
        return int(pos / self.l0step)

    def __init__(self):
        self.l0 = dok_matrix((self.l0H, self.l0W)) #, dtype=np.int8)
        add_points_from_all(self.l0, self.l0step, self.all_gpx)
        self.info.append(self.l0.sum())
        self.info.append(len(self.l0.nonzero()[0]))
        self.view_y = self.index(45.430859)
        self.view_x = self.index(4.3859)

        self.l1 = dok_matrix((self.l0H//2, self.l0W//2)) #, dtype=np.int8)
        add_points_from_all(self.l1, self.l0step*2, self.all_gpx)

        self.l2 = dok_matrix((self.l0H//4, self.l0W//4)) #, dtype=np.int8)
        add_points_from_all(self.l2, self.l0step*4, self.all_gpx)

    def do_compute_image(self, level, vx, vy, vw, vh):
        scale = 2**level
        x = vx//scale
        y = vy//scale
        w = vw//scale
        h = vh//scale
        arr = getattr(self, 'l'+str(level))[y:y+h,x:x+w]
        arr = arr[::-1, :]
        arr /= arr.tocsr().max()
        res = [(int(u), int(v), int(arr[u,v]*100)) for (i,(u,v)) in enumerate(zip(*(arr.nonzero())))] # sparse: list of (i,j,v)
        return res

    def computed_image0(self):
        return self.do_compute_image(0, self.view_x, self.view_y, self.view_w, self.view_h)

    def computed_image1(self):
        return self.do_compute_image(1, self.view_x, self.view_y, self.view_w, self.view_h)

    def computed_image2(self):
        return self.do_compute_image(2, self.view_x, self.view_y, self.view_w, self.view_h)

    @vuejspython.atomic # BUG
    def offset_view(self, dx, dy):
        self.view_x += int(dx)
        self.view_y += int(dy)

vuejspython.start(App(), py_port=42989)


