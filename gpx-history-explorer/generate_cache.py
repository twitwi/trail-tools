
import numpy as np
import gpx_parser as parser
from scipy.sparse import dok_matrix
import json
import glob

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

gpx202004 = "2020-04-01_18-12-43.gpx 2020-04-02_17-06-33.gpx 2020-04-03_18-24-53.gpx 2020-04-04_17-54-45.gpx 2020-04-05_14-40-36.gpx 2020-04-06_16-47-31.gpx 2020-04-07_17-31-36.gpx 2020-04-08_18-13-00.gpx 2020-04-09_17-00-11.gpx 2020-04-11_08-17-22.gpx 2020-04-10_08-18-37.gpx 2020-04-12_21-50-04.gpx".split()
gpx202003corona = "2020-03-24_07-36-50.gpx 2020-03-25_17-04-03.gpx 2020-03-26_16-45-03.gpx 2020-03-27_16-59-29.gpx 2020-03-28_17-20-13.gpx 2020-03-29_15-03-27.gpx 2020-03-30_17-47-48.gpx 2020-03-31_18-32-40.gpx".split()

unit_m = 1e-5
l0step = 2.5 * unit_m
l0H = int(180/l0step) +1
l0W = int(2*l0H) +1
#all_gpx = gpx202004 + gpx202003corona
all_gpx = glob.glob('*.gpx')

def index(self, pos):
    return int(pos / l0step)

l0 = dok_matrix((l0H, l0W)) #, dtype=np.int8)
add_points_from_all(l0, l0step, all_gpx)
l0 /= l0.tocsr().max()
#view_y = index(45.430859)
#view_x = index(4.3859)

res = {
    str(u) + '/' + str(v) : int(l0[u,v]*100)
    for (i,(u,v)) in enumerate(zip(*(l0.nonzero())))
}
mass = l0.sum()
cu = l0step*sum((
    u*l0[u,v]
    for (i,(u,v)) in enumerate(zip(*(l0.nonzero())))
    )) / mass
cv = l0step*sum((
    v*l0[u,v]
    for (i,(u,v)) in enumerate(zip(*(l0.nonzero())))
    )) / mass
res['info'] = {
    "step": l0step,
    "all_gpx": all_gpx,
    "cu": cu,
    "cv": cv,
}

with open('cache.json', 'w') as f:
    json.dump(res, f, indent=2)
