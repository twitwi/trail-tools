import sys
import numpy as np
from matplotlib import pyplot as plt

import datetime
import matplotlib.dates as mdates
import matplotlib.units as munits
converter = mdates.ConciseDateConverter()
munits.registry[np.datetime64] = converter
munits.registry[datetime.date] = converter
munits.registry[datetime.datetime] = converter

import os
import hrm
import steps

env_value = None
def has_env(k):
    global env_value
    env_value = None
    if k in os.environ:
        env_value = os.environ[k]
        return True
    else:
        return False


def main(argv):
    if len(argv)>1:
        fnames = argv[1:]
    else:
        fnames = ['AnyTrack-STEPS.db', 'AnyTrack-HRM.db']

    trunc_start = None
    if has_env('FROM'):
        trunc_start = int((np.datetime64(env_value) - np.datetime64('1970-01-01T00:00')) / np.timedelta64(1, 's'))
    trunc_end = None
    if has_env('TO'):
        trunc_end = int((np.datetime64(env_value) - np.datetime64('1970-01-01T00:00')) / np.timedelta64(1, 's'))

    alldatarr = []
    infos = []
    for f in fnames:
        if f[-3:]=='.db' and 'HRM' in f:
            bpm, rr = hrm.load(f, start_at=trunc_start, end_at=trunc_end)
            if bpm.shape[0] > 1:
                alldatarr.append(bpm)
                infos.append(f + '[bpm]')
            if rr.shape[0] > 1:
                alldatarr.append(rr)
                infos.append(f + '[rr]')
        elif f[-3:]=='.db' and 'STEPS' in f:
            stp = steps.load(f, start_at=trunc_start, end_at=trunc_end)
            alldatarr.append(stp)
            infos.append(f + '[steps]')
        elif f[-3:]=='.db':
            print("Expects .db to contain either STEPS or HRM, skipping", f)
        else:
            csv = np.genfromtxt(f, delimiter=',')
            alldatarr.append(csv[:,:3])
            infos.append(f + '[csv]')

    print(infos)
    print([d.shape for d in alldatarr])
    alldate = [np.array(list(map(lambda v: datetime.datetime.fromtimestamp(v), d[:, 0]))) for d in alldatarr]

    ax1 = plt.gcf().add_subplot(111) # steps and hrm
    ax2 = ax1.twinx() # intraRR
    ax3 = ax1.twinx() 
    def skip(*axs, label=None):
        for ax in axs:
            ax.plot([], [], label=label if ax==ax1 else None)

    for i, data in enumerate(alldatarr):
        ad = alldate[i]
        nosuff = ''
        def has_suffix(s):
            nonlocal nosuff
            nosuff = infos[i][:-len(s)]
            return s in infos[i]
        if False: pass
        elif has_suffix('[steps]'):
            p = ax1.plot(ad, data[:, 1], alpha=0.33, label="Steps: " + nosuff)
            c = p[0].get_color()
            skip(ax2, ax3)
            ax1.grid(color=c, linestyle='dashed')
            ax1.tick_params(axis='y', colors=c)
            #ax1.set_ylim(0, (np.max(data[:,1])//100+1)*100)
            if True:
                n = 3 # every 30s as the recorder targets one point every 10 sec
                chunk = np.copy(data[::n, 2])
                chunk[1:] = np.diff(chunk)
                halfdelta = (ad[n]-ad[0])/2 #n/2*(ad[-1]-ad[0])/(len(ad)-1)
                cdate = np.array(ad[::n] + halfdelta, dtype='datetime64')
                chunk[1:] = chunk[1:] / (np.diff(cdate) / np.timedelta64(60, 's'))
                #plt.bar(xdate[::n] - (xdate[n] - xdate[0]), chunk, xdate[n]-xdate[0], **kwargs)
                ax1.plot(ad[::n], chunk, color=c)
        elif has_suffix('[bpm]'):
            p = ax1.plot(ad, data[:, 1], label="Report BPM: " + nosuff)
            c = p[0].get_color()
            skip(ax2, ax3)
            ax1.grid(color=c, linestyle='dotted')
            ax1.tick_params(axis='y', colors=c)
            #ax1.set_ylim(0, (np.max(data[:,1])//100+1)*100)
        elif has_suffix('[rr]'):
            p = ax3.plot(ad, data[:, 1], ls='dotted')
            c = p[0].get_color()
            ax3.tick_params(axis='y', colors=c)
            skip(ax1, ax2, label='Intra RR: ' + nosuff)
            #ax1.plot(rr[:, 0], 60000/rr[:, 1], label="bpm from intra RR")
        elif has_suffix('[csv]'):
            p = ax1.plot(ad, data[:, 1], label="Steps: " + nosuff)
            c = p[0].get_color()
            skip(ax2, ax3)
            ax1.grid(color=c, linestyle='dashed')
            ax1.tick_params(axis='y', colors=c)
            #ax1.set_ylim(0, (np.max(data[:,1])//100+1)*100)


    #plt_all = plt_bpm+plt_irr
    #ax2.legend(plt_all, [p.get_label() for p in plt_all])
    ax1.legend()

    if has_env('SAVEFIG'):
        plt.savefig(env_value)
        print('Saved figure as', env_value)
    else:
        plt.show()


main(sys.argv)



