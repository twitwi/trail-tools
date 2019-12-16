
import numpy as np

mute = lambda *l, **kw: None

from scipy.ndimage import convolve1d
def smooth(a, n):
    kernel = np.ones(n) / (n+0.)
    return convolve1d(a, kernel, axis=0, mode='reflect')


def load(fname, print=mute, start_at=None, end_at=None):
    """
    Loads a file with optional intraRR sequence, as in
                date        bpm                    intraRR

    HRMSample(1573380768423, 84, 3, false, false, "705/373")
    HRMSample(1573380769444, 85, 3, false, false, "687")
    HRMSample(1573380770474, 85, 3, false, false, "")

    Produces two arrays (one with bpm, one with intraRR), each as a (T,3),
    with (timestamp, value, cumulated_value)
    """
    start_at = 0 if start_at is None else start_at
    end_at = 1573163452*4 if end_at is None else end_at
    data = []
    rr = []
    false = False
    true = True
    t = -1
    anyt = -1
    def HRMSample(ts1000, bpm, status, hummm, has_hrm, intrarr):
        nonlocal anyt
        nonlocal t
        ts = ts1000/1000
        if anyt == -1:
            anyt = ts
        if not(start_at < ts < end_at):
            return
        anyt = ts
        data.append([ts, bpm, bpm])
        if len(intrarr) > 0:
            for irr in intrarr.split("/"):
                irr = int(irr)
                if t == -1:
                    t = ts - 0.500
                t = t+irr/1000
                if ts-1.000 > t:
                    print("Break time at", ts-1.000, t)
                    rr.append([t, 0, 0])
                    t = ts-1.000
                    rr.append([t, 0, 0])
                rr.append([t, irr, irr])

    with open(fname) as f:
        for l in f.readlines():
            l = l[len('HRMSample('):-2].split(',')
            HRMSample(int(l[0]), int(l[1]), 3, True, True, l[5][2:-1])
            #eval(l[:-1])

    data = np.array(data)
    if data.shape == (0,):
        data = np.array([[anyt, 0, 0]])
    data[:,2] = np.cumsum(data[:,1])

    rr = np.array(rr)
    if rr.shape == (0,):
        rr = np.array([[data[0,0], 0, 0]])
    rr[:,2] = np.cumsum(rr[:,1])

    print(data.shape)
    return data,rr
