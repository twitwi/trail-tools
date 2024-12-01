import marimo

__generated_with = "0.8.16"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import numpy as np
    import sys
    import lxml.etree as ET
    import re
    #from collections import namedtuple
    from typing import NamedTuple
    from collections import defaultdict
    from scipy.stats import rankdata
    import pandas as pd
    import altair as alt

    from livetrail_timedist import compute_segments, load_xml, RacePoint_from_Element, parcours_hours, passage_hours

    import matplotlib.pyplot as plt
    return (
        ET,
        NamedTuple,
        RacePoint_from_Element,
        alt,
        compute_segments,
        defaultdict,
        load_xml,
        mo,
        np,
        parcours_hours,
        passage_hours,
        pd,
        plt,
        rankdata,
        re,
        sys,
    )


@app.cell
def __():
    BOF = '495' # bibs of focus
    BOI = '' # bibs of interest
    RACE_TIME = 1 # set to 0 for hour of passage instead
    RELATIVE = 0 # relative time instead of absolute one (everyone takes 100h)
    EFFORT = 0
    FIRST_CHECKPOINT = 1
    LAST_CHECKPOINT = -1
    return (
        BOF,
        BOI,
        EFFORT,
        FIRST_CHECKPOINT,
        LAST_CHECKPOINT,
        RACE_TIME,
        RELATIVE,
    )


@app.cell
def __():
    table_files = []
    table_files += ['data/livetrail-echappeebelle2024-152km--table.xml']
    table_files += ['data/livetrail-echappeebelle2024-150Shun--table.xml']
    return table_files,


@app.cell
def __(
    RACE_TIME,
    RacePoint_from_Element,
    load_xml,
    parcours_hours,
    passage_hours,
    pd,
    re,
    table_files,
):
    # temps de passage

    passages = []

    for ifile,table_file in enumerate(table_files):
        m = re.match(r'(.*)-([^-]*)--table.xml', table_file)
        parcours_file = m.group(1) + '--parcours.xml'
        subid = m.group(2)

        pxml = load_xml(parcours_file)
        subpoints = pxml.xpath(f'//points[@course="{subid}"]/pt')
        subpoints = [RacePoint_from_Element(s) for s in subpoints]
        subpoints = {s.id: s for s in subpoints}
        #print(subpoints)

        xml = load_xml(table_file)
        bibs = xml.xpath('//lignes/l')

        for ibib,bib in enumerate(bibs):
            info = dict(ibib=ibib, bib=bib.attrib['doss'], ifile=ifile)
            base_d = int(subpoints[0].hfirst.split('-')[0])
            delta_d = None
            base_h = prev_h = parcours_hours(subpoints[0].hfirst)
            for pas in bib.xpath('./p'):
                a = lambda n: pas.attrib[n]
                if delta_d is None and a('j') != '': # j="" for DNS
                    delta_d = int(a('j')) - base_d
                if a('h') is None or a('h') == '': # drop out
                    continue
                cur_id = int(a('idpt'))
                cur_h = (int(a('j')) - delta_d) * 24 + passage_hours(a('h'))
                if cur_id == 0 and RACE_TIME:
                    base_h = cur_h # we have a per-person starting hour
                info[f'p{cur_id}'] = cur_h - base_h
                prev_id = cur_id
                prev_h = cur_h
            passages.append(info)

    dfpassages = pd.DataFrame(passages)
    dfpassages.rename(columns={f'p{k}': s.name for [k,s] in subpoints.items()})
    return (
        a,
        base_d,
        base_h,
        bib,
        bibs,
        cur_h,
        cur_id,
        delta_d,
        dfpassages,
        ibib,
        ifile,
        info,
        m,
        parcours_file,
        pas,
        passages,
        prev_h,
        prev_id,
        pxml,
        subid,
        subpoints,
        table_file,
        xml,
    )


@app.cell
def __(BOF, alt, dfpassages, mo, np, pd):
    def _():
        last = 'p80'
        df = dfpassages
        if False: # no shunt
            df = df[dfpassages.ifile==0]
        df = df.rename(columns={f'p{i}': f'p0{i}' for i in range(10)})
        if False: # only finishers
            df = dfpassages[dfpassages[last]>0] 
        ravitos = df.columns[3:]
        columns = []
        faster = []
        slower = []
        fasterwilldrop = []
        slowerwilldrop = []
        moreconservative = []
        lessconservative = []
        dropped = []
        boflast = df[df.bib == BOF][last].values[0]
        isfinisher = (1-df[last].isna())
        isfasterlast = df[last] < boflast
        if False: #ignore what???
            df = df[np.logical_not(isfasterlast)]
            isfasterlast = df[last] < boflast
        for first in df.columns.values[3+1:]:
            boffirst = df[df.bib == BOF][first].values[0]
            isfasterfirst = df[first] < boffirst
            isok = 1 - df[first].isna()
            columns.append(first)
            dropped.append(np.sum(1-isok))
            faster.append(np.sum(isfinisher * isfasterfirst * isfasterlast))
            slower.append(np.sum(isfinisher * (1-isfasterfirst) *  (1- isfasterlast)))
            fasterwilldrop.append(np.sum(isok * (1-isfinisher) * isfasterfirst))
            slowerwilldrop.append(np.sum(isok * (1-isfinisher) * (1-isfasterfirst)))
            moreconservative.append(np.sum(isfinisher * isok * (1-isfasterfirst) * isfasterlast))
            lessconservative.append(np.sum(isfinisher * isok * isfasterfirst * (1-isfasterlast)))

        curves = pd.DataFrame([faster, slower, fasterwilldrop, slowerwilldrop, moreconservative, lessconservative, dropped],
                              index=['a) Faster', 'b) Slower', 'x) Faster (drop)', 'y) Slower (drop)', 'c) MoreCons.', 'd) LessCons.', 'z) Drop'],
                              columns=columns)
        curves = curves.stack().reset_index()
        curves.columns = ['quad', 'step', 'count']
        #return curves
        return mo.ui.altair_chart(alt.Chart(curves).mark_area().encode(
            x=alt.X('step'),
            y=alt.Y('count'),
            color='quad',
        ))

    _()
    return


@app.cell
def __(BOF, alt, dfpassages, mo, np, pd):
    def _():
        last = 'p80'
        df = dfpassages.rename(columns={f'p{i}': f'p0{i}' for i in range(10)})
        if False: # only finishers
            df = dfpassages[dfpassages[last]>0] 
        ravitos = df.columns[3:]
        columns = []
        faster = []
        slower = []
        moreconservative = []
        lessconservative = []
        dropped = []
        boflast = df[df.bib == BOF][last].values[0]
        isfasterlast = (1-df[last].isna()) * (df[last] < boflast)
        if False: #ignore what???
            df = df[np.logical_not(isfasterlast)]
            isfasterlast = df[last] < boflast
        for first in df.columns.values[3+1:]:
            boffirst = df[df.bib == BOF][first].values[0]
            isfasterfirst = df[first] < boffirst
            isok = 1 - df[first].isna()
            columns.append(first)
            dropped.append(np.sum(1-isok))
            faster.append(np.sum(isok * isfasterfirst * isfasterlast))
            slower.append(np.sum(isok * (1-isfasterfirst) *  (1- isfasterlast)))
            moreconservative.append(np.sum(isok * (1-isfasterfirst) * isfasterlast))
            lessconservative.append(np.sum(isok * isfasterfirst * (1-isfasterlast)))

        curves = pd.DataFrame([faster, slower, moreconservative, lessconservative, dropped],
                              index=['a) Faster', 'e) Slower', 'd) MoreCons.', 'c) LessCons.', 'b) Drop'],
                              columns=columns)
        curves = curves.stack().reset_index()
        curves.columns = ['quad', 'step', 'count']
        #return curves
        return mo.ui.altair_chart(alt.Chart(curves).mark_area().encode(
            x=alt.X('step'),
            y=alt.Y('count'),
            color='quad',
        ))

    #_()
    return


@app.cell
def __(BOF, alt, dfpassages, mo, subpoints):
    _df = dfpassages.rename(columns={f'p{k}': s.name for [k,s] in subpoints.items()})
    _nx = alt.binding_select(options=_df.columns.values[3:])
    _px = alt.param(value = _nx.options[1], name='first', bind=_nx)
    _ny = alt.binding_select(options=_df.columns.values[3:])
    _py = alt.param(value = _ny.options[-1], name='last', bind=_ny)
    _col= alt.condition(alt.datum.bib == int(BOF), alt.value('red'), 'ifile')
    _ch = alt.Chart(_df).mark_point().encode(x='x:Q', y='y:Q', color=_col, opacity=alt.value(0.5)).transform_calculate(x=f'datum[first]', y=f'datum[last]').add_params(_px, _py)
    mo.ui.altair_chart(_ch)
    return


@app.cell
def __(dfpassages, subpoints):
    dfpassages.rename(columns={f'p{k}': s.name for [k,s] in subpoints.items()}).plot.scatter('R1 Arselle', 'Arrivée Aiguebelle', c='ifile', cmap='jet', s=10, alpha=0.5,)
    return


@app.cell
def __(BOF, dfpassages, pd, plt, subpoints):
    dfranks = dfpassages.copy()
    dfranks = dfranks[dfranks.p80 > 0]
    _ = dfranks.copy()
    dfranks = dfranks.rank(axis=0)
    dfranks.bib = _.bib
    dfranks.ibib = _.ibib
    dfranks.ifile = _.ifile
    #dfranks
    plt.plot(dfranks[dfranks.bib==BOF].values[0, 3+1:], label='(all)')

    _res = dfranks[dfranks.bib==BOF]


    dfranks = dfpassages.copy()
    dfranks = dfranks[dfranks.ifile == 0]
    dfranks = dfranks[dfranks.p80 > 0]
    _ = dfranks.copy()
    dfranks = dfranks.rank(axis=0)
    dfranks.bib = _.bib
    dfranks.ibib = _.ibib
    dfranks.ifile = _.ifile
    #dfranks
    plt.plot(dfranks[dfranks.bib==BOF].values[0, 3+1:], label="(sans shunt)")
    print(len(subpoints), subpoints)
    #plt.xticks(range(len(subpoints)-1), [f'{s.name}- -' for [k,s] in list(subpoints.items())[1:]], rotation=45, ha='right', )
    _cols = dfranks.rename(columns={f'p{k}': s.name for [k,s] in subpoints.items()}).columns[3+1:]
    plt.xticks(range(len(_cols)), [f'{k}- -' for k in _cols], rotation=45, ha='right')
    plt.grid()
    plt.legend()
    plt.ylabel('place parmi les finishers')
    plt.ylim(0, None)
    plt.show()

    _res = pd.concat([_res, dfranks[dfranks.bib==BOF]], axis=0)
    _res.rename(columns={f'p{k}': s.name for [k,s] in subpoints.items()})
    return dfranks,


@app.cell
def __():
    """
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
        #print(subpoints)

        xml = load_xml(table_file)
        bibs = xml.xpath('//lignes/l')
        print(len(bibs))
        strain_curves = []
        # for ranking
        ibof = 0
        xbof = []
        alllines = []

        for ibib,bib in enumerate(bibs):
            segs = compute_segments(subpoints, bib, RACE_TIME)
            if len(segs) == 0:
                continue

            if len(segs)>0 and segs[0].idfrom != 0:
                print(segs)
            at = FIRST_CHECKPOINT - 1 # first ravito, not checking its id actually
            if len(segs) > at:
                times_at_first.append(segs[at].cumul_dur)
                try:
                    times_at_last.append(segs[LAST_CHECKPOINT].cumul_dur)
                except:
                    times_at_last.append(segs[-1].cumul_dur)
                colors.append(segs[0].idfrom * 100 + segs[-1].idto)
                dosss.append(bib.attrib['doss'])
            x1s = np.array([s.cumul_dist for s in segs])
            x2s = np.array([s.cumul_strain(150) for s in segs])
            if EFFORT:
                usexs = x2s # effort
            else:
                usexs = x1s # distance
            ys = np.array([s.cumul_dur for s in segs])
            if RELATIVE and ys.size>0:
                ys /= ys[-1] / 100
            more = dict(alpha = 0.03)
            try:
                lstyles = ['solid', 'dashed']
                bnum = bib.attrib['doss']
                if bnum in BOF.split(' '):
                    more = dict(alpha = .9, label=f"/ {bnum}", color="k", ls="dotted")
                    ibof = ibib
                    xbof = usexs
                elif bnum in BOI.split(' '):
                    more = dict(alpha = .9, label=bnum, ls=lstyles[int(bnum)%2])
            finally: pass
            #plt.plot(x1s, ys, **more)
            plt.plot(usexs, -ys, **more)
            alllines.append(ys)

    alllines.append(alllines.pop(ibof))
    lmax = np.max([len(l) for l in alllines])
    finishinglines = [l for l in alllines if len(l) == lmax]
    print(len(alllines), len(finishinglines))
    #ranks = np.argsort(np.argsort(finishinglines, axis=0), axis=0)
    ranks = rankdata(finishinglines, axis=0)
    #ranks = ranks[ranks[:,-1]>230] 

    plt.plot(xbof, ranks[-1:].T, alpha=0.5)

    plt.grid()
    plt.legend(loc=0)
    plt.show()
    """
    return


@app.cell
def __(
    BOF,
    BOI,
    FIRST_CHECKPOINT,
    LAST_CHECKPOINT,
    colors,
    dosss,
    minmax,
    plt,
    subpoints,
    times_at_first,
    times_at_last,
):
    def _():
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
        plt.xlabel(f'T First, {list(subpoints.values())[FIRST_CHECKPOINT].name}')
        plt.ylabel(f'T Final, {list(subpoints.values())[LAST_CHECKPOINT].name})')
        plt.legend()
        plt.show()
    _()
    return


@app.cell
def __(alllines, pd, subpoints):
    df = pd.DataFrame(alllines, columns=[p.name for p in subpoints.values()][1:])
    df
    return df,


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
