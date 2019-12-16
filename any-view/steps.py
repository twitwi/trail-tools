
import numpy as np

mute = lambda *l, **kw: None


def load(fname, print=mute, start_at=None, end_at=None):
    """
    Loads a file with steps, as in
                date           cumulated, instant

    StepsSample(1573163452606, 188169, 13)
    StepsSample(1573163462606, 188169, 0)

    Produces one array (T,3),
    with (timestamp, value, cumulated_value)
    """
    start_at = 0 if start_at is None else start_at
    end_at = 1573163452*4 if end_at is None else end_at
    data = []
    with open(fname) as f:
        for l in f.readlines():
            l = l[len('StepsSample('):-2].split(',')
            w = int(l[0])/1000
            if start_at < w < end_at:
                data.append([w, int(l[2]), 0])

    data = np.array(data)
    data[:,2] = np.cumsum(data[:,1])

    return data
