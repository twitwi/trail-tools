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
                #np.savetxt('/tmp/hrm.csv', bpm, delimiter=',')
                alldatarr.append(bpm)
                infos.append(f + '[bpm]')
            if rr.shape[0] > 1:
                if False: # wip explore rr fix
                    ax1 = plt.gcf().add_subplot(2,1,1)
                    for st in [1, 2, 3]:
                        d = rr[st:,2]-rr[:-st,2]
                        ax1.scatter(rr[:-st,0], d, label="δ="+str(st))
                    ax1.legend()
                    ax2 = plt.gcf().add_subplot(2,1,2)
                    def on_xlims_change(event_ax):
                        print('re')
                        start, stop = event_ax.get_xlim()
                        candidates = np.array([])
                        for st in [1, 2, 3]:
                            rrr = rr[(start<rr[:,0])&(rr[:,0]<stop), 2]
                            d = rrr[st:]-rrr[:-st]
                            candidates = np.concatenate((candidates, d))
                            print(candidates.shape)
                        c = np.bincount(candidates.astype(np.int64))
                        ax2.clear()
                        ax2.plot(np.arange(c.size), c)
                        c = np.cumsum(c)
                        #ax2.plot(np.arange(c.size), c)
                        st = 200
                        c = c[st:] - c[:-st]
                        #ax2.hist(candidates, bins=100)
                        #ax2.bar(np.arange(c.size), c, align='edge')
                        hst = st/2
                        xm = np.argmax(c)
                        ax2.plot(np.arange(c.size), c)
                        ax2.scatter([(xm+hst)/3-hst, (xm+hst)/2-hst, xm, 2*(xm+hst)-hst, 3*(xm+hst)-hst], [c[xm]]*5, marker='o', color="r")
                        ax2.grid()
                        
                    ax1.callbacks.connect('xlim_changed', on_xlims_change)
                    plt.show()
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
    # Log HRV (VFC) on zoom change
    def compute_measures(rr, only=None):
        if type(only) == str:
            only = [only]
        o = {}
        def set(k, computev):
            nonlocal o
            if only is None or k in only:
                o[k] = computev()
            else:
                o[k] = 0
        p = lambda v: float('%.2f' % v)
        ###### TEST
        #####rr = (rr[2:]+rr[1:-1]+rr[:-2])/3
        ######
        rrdiff = np.diff(rr)
        set('sdnn', lambda: p(np.std(rr)))
        set('sdsd', lambda: p(np.std(rrdiff)))
        set('pnn50', lambda: p(100 * np.sum(np.abs(rrdiff)>50) / rrdiff.size))
        set('pnn100', lambda: p(100 * np.sum(np.abs(rrdiff)>100) / rrdiff.size))
        set('rmssd', lambda: p(np.mean(rrdiff**2)**0.5))
        # see: "Heart rate variability: a measure of cardiac autonomic tone"
        set('my-n-rmssd', lambda: p(100 * np.mean((rrdiff*2/(rr[1:]+rr[:-1]))**2)**0.5))
        set('my-n-d', lambda: p(100 * np.mean(np.abs(rrdiff*2/(rr[1:]+rr[:-1])))))
        for pc in [50, 75, 90]:
            set('my-n-d-'+str(pc)+'%', lambda: p(100 * np.percentile(np.abs(rrdiff*2/(rr[1:]+rr[:-1])), [pc])))
        return o
    def on_xlims_change(event_ax):
        for i, data in enumerate(alldatarr):
            s = '[rr]'
            if infos[i][-len(s):] != s: continue
            ad = alldate[i]
            start, stop = event_ax.get_xlim()
            start = mdates.num2date(start)
            stop = mdates.num2date(stop)
            start = start.replace(tzinfo=None)
            stop = stop.replace(tzinfo=None)
            rr = data[(start<ad) & (ad<stop), 1]
            rr = rr[rr>0]
            if rr.size == 0: continue
            o = compute_measures(rr)
            import json
            print("HRV on", rr.size, "values:", json.dumps(o))
    ax1.callbacks.connect('xlim_changed', on_xlims_change)
    # heatmap stuff ########
    from matplotlib.widgets import Button, Slider
    heatmap = None
    heatmap_axis = None
    heatmap_colorbar = None
    heatmap_keys = None
    heatmap_current = 0
    hide_diagonal = 1 # iterate over i=0..end and j=i+X...end
    but1 = None
    but2 = None
    slid1 = None
    def update_hide_diagonal(v):
        nonlocal hide_diagonal
        hide_diagonal = v
        update_heatmap()
    def next_key(ev):
        if heatmap_keys is None: return
        l = len(heatmap_keys)
        nonlocal heatmap_current
        heatmap_current = (heatmap_current + 1) % l
        update_heatmap()
    def previous_key(ev):
        if heatmap_keys is None: return
        l = len(heatmap_keys)
        nonlocal heatmap_current
        heatmap_current = (heatmap_current + l - 1) % l
        update_heatmap()
    def add_button(fig, xywh, text, cb):
        axbutton = fig.add_axes(xywh)
        button = Button(axbutton, text)
        if cb is not None:
            button.on_clicked(cb)
        return button
    def update_heatmap(N=40):
        if heatmap is None: return
        nonlocal heatmap_axis
        if heatmap_axis is None:
            ax = heatmap.add_subplot(111)
            heatmap_axis = ax
        else:
            ax = heatmap_axis
            ax.clear()
        nonlocal but1,but2,slid1
        if but1 is None:
            but1 = add_button(heatmap, [0.7, 0.9, 0.05, 0.05], '«', previous_key)
            but2 = add_button(heatmap, [0.75, 0.9, 0.05, 0.05], '»', next_key)
            slid1 = Slider(ax=plt.axes([0.2, 0.95, 0.6, 0.05]),
                           label='Hide Diagonal',
                           valmin=1,
                           valmax=N-5,
                           valstep=1,
                           valinit=hide_diagonal)
            slid1.on_changed(update_hide_diagonal)
        for i, data in enumerate(alldatarr):
            s = '[rr]'
            if infos[i][-len(s):] != s: continue
            ad = alldate[i]
            start, stop = ax1.get_xlim()
            # actually compute the grid
            a = np.zeros((N,N))
            # brute force...
            for i,sta in enumerate(np.linspace(start, stop, N)):
                sta = mdates.num2date(sta)
                sta = sta.replace(tzinfo=None)
                for j,sto in list(enumerate(np.linspace(start, stop, N)))[i+hide_diagonal:]:
                    sto = mdates.num2date(sto)
                    sto = sto.replace(tzinfo=None)
                    rr = data[(sta<ad) & (ad<sto), 1]
                    rr = rr[rr>50]
                    if rr.size == 0: continue
                    nonlocal heatmap_keys
                    m = compute_measures(rr, only=heatmap_keys[heatmap_current] if heatmap_keys is not None else None)
                    heatmap_keys = list(m.keys())
                    k = heatmap_keys[heatmap_current%len(heatmap_keys)]
                    ax.set_title(k)
                    a[i,j] = m[k]
            plt.sca(ax)
            plt.imshow(a)
            nonlocal heatmap_colorbar
            if heatmap_colorbar is not None: heatmap_colorbar.remove()
            heatmap_colorbar = plt.colorbar()
            plt.contour(a, cmap='Greys')
            heatmap.show()
            heatmap.canvas.draw_idle()
    def open_heatmap(ev):
        nonlocal heatmap
        heatmap = plt.figure('heatmap') if heatmap is None else heatmap
        heatmap.show()
        update_heatmap()
    but = add_button(plt.gcf(), [0.7, 0.9, 0.2, 0.075], 'Heatmaps', open_heatmap)
    #########################
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
            ax1.grid()
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



