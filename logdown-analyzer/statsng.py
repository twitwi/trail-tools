import marimo

__generated_with = "0.8.0"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo

    """ TODOS

    - import hr data, hrzones histgrams (like daily steps), +efficiency (hr vs effective speed)
    - equivalent distance
    - make the advanced colorbar_scale optional + set better defaults for non-dayly
    """
    return mo,


@app.cell(hide_code=True)
def __(mo):
    def MOLIVE(interval="1s", verbose=False):
        import importlib
        import os
        modules = {}
        lstamp = {}
        def _maybe_refresh(ev):
            updated = []
            for k,mod in modules.items():
                _stamp = os.stat(mod.__file__).st_mtime
                if _stamp != lstamp[k] or module_has_dependencies_on_any(mod, updated):
                    lstamp[k] = _stamp
                    importlib.reload(mod)
                    updated.append(mod.__name__)
            if len(updated) > 0:
                if verbose:
                    print("UPDATED:", updated)
                lset(lambda v: v+1)
        def add_import(*modnames):
            res = []
            for name in modnames:
                if name in modules:
                    # change iteration order so that last imported come last
                    mod = modules[name]
                    del modules[name]
                    modules[name] = mod
                else:
                    modules[name] = importlib.import_module(name)
                    lstamp[name] = os.stat(modules[name].__file__).st_mtime
                res.append(modules[name])
            return res[0] if len(res) == 1 else res
        lget, lset = mo.state(0)
        setattr(lget, 'import_all', add_import)
        lrefresh = mo.ui.refresh(options=[interval, '10s'], default_interval=None, on_change=_maybe_refresh)
        return lrefresh, lget

    def module_has_dependencies_on_any(mod, others):
        if len(others) == 0:
            return False
        deps = set([el.__module__ for el in mod.__dict__.values() if hasattr(el, '__module__')])
        others = set(others)
        return not deps.isdisjoint(others)

    def show_table(th, title=None, round=6, **more):
        import pandas as pd
        df = pd.DataFrame(th.detach().numpy().tolist())
        df = df.round(round)
        df.columns = ['_' for i in range(len(df.columns))]
        if not 'label' in more and title is not None:
            more['label'] = f'{title} (shape: {th.shape})'
        return mo.ui.table(data=df, **more)

    #mo.md("""## Setting up live reload on python change (+ mo utils)""")
    return MOLIVE, module_has_dependencies_on_any, show_table


@app.cell
def __(MOLIVE):
    lrefresh, live = MOLIVE(verbose=True) #; lrefresh
    return live, lrefresh


@app.cell
def __(mo, runShellCommand):
    refreshOnLoadSeq, setLoadSeq = mo.state(0)
    showWeeklyDetails = mo.ui.checkbox(True, label='Show details')
    showOnlyRecent = mo.ui.checkbox(True, label='Limit to recent')
    buttonReload = mo.ui.button(on_click=lambda ev: setLoadSeq(lambda v: v + 1), label='↺', tooltip='Reload log file')
    buttonEditLogs = mo.ui.button(on_click=lambda ev: runShellCommand('edit-logs', ev), label='L', tooltip='Edit log file')
    buttonEditNotes = mo.ui.button(on_click=lambda ev: runShellCommand('edit-notes', ev), label='N', tooltip='Edit notes')
    buttonRaces = mo.ui.button(on_click=lambda ev: runShellCommand('edit-races', ev), label='R', tooltip='Edit races')
    buttonEditPT = mo.ui.button(on_click=lambda ev: runShellCommand('edit-parcourstest', ev), label='PT', tooltip='Edit parcours test')
    return (
        buttonEditLogs,
        buttonEditNotes,
        buttonEditPT,
        buttonRaces,
        buttonReload,
        refreshOnLoadSeq,
        setLoadSeq,
        showOnlyRecent,
        showWeeklyDetails,
    )


@app.cell
def __(
    buttonEditLogs,
    buttonEditNotes,
    buttonEditPT,
    buttonRaces,
    buttonReload,
    mo,
    showOnlyRecent,
    showWeeklyDetails,
    total,
    ui_executor,
    ui_monthly,
    ui_shoely,
    ui_weekly,
    ui_yearly,
):
    ui_tabs = dict()

    ui_tabs['Weekly'] = ui_weekly
    ui_tabs['Monthly'] = ui_monthly
    ui_tabs['Yearly'] = ui_yearly
    ui_tabs['Shoely'] = ui_shoely

    ui_tabs['About'] = 'Bla bla...'

    mo.vstack([
        mo.hstack([
            showWeeklyDetails, showOnlyRecent,
            mo.hstack([buttonReload, buttonEditLogs, buttonEditNotes, buttonEditPT, buttonRaces, ui_executor]),
            f'Total: {total.dist} km | {total.dur // 60} h | D+ {total.d_pos} m | D- {total.d_neg} m',
        ]),
        mo.ui.tabs(
            ui_tabs,
            lazy=True,
        ),
    ])
    return ui_tabs,


@app.cell
def __():
    style_table = """
    <style>
        table {
            width: 100%;
        }
        .with-actions { white-space: nowrap; }
        td { padding: 0.2em 0.5em; }
        td.w2-0 { background: teal; color: white; }
        td.w2-1 { background: grey; color: white; }

        td.w, td.w~* { border-top: 1px solid black; }
        td.w+*+*+*+* { border-right: 1px solid black; }
        td:last-child { border-right: 1px solid black; }
        td:nth-last-child(-n+3) { font-size: 70%; }
        .graded {
            position: relative;
            &::after {
                content: '';
                --color: darkblue;
                background: linear-gradient(white, white 3px, var(--color) 5px, var(--color));
                background: var(--color);
                position: absolute; left: 2%; width: calc(var(--v) * 96%); bottom: 0; height: 100%/*.3em*/;
                opacity: 0.15;
            }
            &.dur::after { --color: darkgreen; }
            &.d_pos::after { --color: darkred; }
        }
    </style>
    """
    return style_table,


@app.cell
def __(
    anywidget,
    entries,
    max_daily_stats,
    max_weekly_stats,
    mo,
    namedtuple_dict,
    np,
    runShellCommand,
    showOnlyRecent,
    showWeeklyDetails,
    style_table,
    traitlets,
    weekly_stats_dict,
):
    def entries_in_week(entries, i, w):
        c = 0
        while i < len(entries) and entries[i]['week'] == w:
            c += 1
            i += 1
        return c

    def duration(tot):
        m = tot % 60
        h = (tot - m) // 60
        res = '{}h{:02}'.format(h, m)
        return res

    def colorbar_scale(v, br, max):
        R = 10
        α = 0.66
        return np.where(v < br,
                        α*v/br,
                        α+(1-α)*np.log(1 + np.maximum(0, R*(v-br)) / (max-br))/np.log(1+R))

    def _ui_weekly(entries, limit=1e10):
        _sp = '&#x202F;'
        res = []
        res.append('<table><tbody>')
        week = 0
        for i,ed in enumerate(entries):
            if i > limit: break
            res.append('<tr>')
            e = namedtuple_dict(ed)
            if i == 0 or e.week != entries[i-1]['week']:
                week += 1
                nb = entries_in_week(entries, i, e.week)
                stat = namedtuple_dict(weekly_stats_dict[e.week])
                st_dist = "--v: " + str(colorbar_scale(stat.dist, 30, max_weekly_stats['dist']))
                st_dur = "--v: " + str(colorbar_scale(stat.dur, 300, max_weekly_stats['dur']))
                st_d_pos = "--v: " + str(colorbar_scale(stat.d_pos, 1000, max_weekly_stats['d_pos']))
                res.append(f'<td class="w w-{week} w2-{week%2} w3-{week%3}" rowspan={nb}>W:{e.week}</td>')
                res.append(f'<td class="graded dist" rowspan="{nb}" style="{st_dist}">{stat.dist}{_sp}km</td>')
                res.append(f'<td class="graded dur" rowspan="{nb}" style="{st_dur}">{duration(stat.dur)}</td>')
                res.append(f'<td class="graded d_pos" rowspan="{nb}" style="{st_d_pos}">{stat.d_pos}{_sp}D+</td>')
                res.append(f'<td class="d_neg" rowspan="{nb}">{stat.d_neg}{_sp}D-</td>')
                res.append(f'<td rowspan="{nb}">{nb}</td>')
            if showWeeklyDetails.value:
                st_dist = "--v: " + str(colorbar_scale(e.dist, 30, max_daily_stats['dist']))
                st_dur = "--v: " + str(colorbar_scale((e.dur or 0), 300, max_daily_stats['dur']))
                st_d_pos = "--v: " + str(colorbar_scale((e.d_pos or 0), 1000, max_daily_stats['d_pos']))
                res.append(f'''<td class="with-actions" title="{'' if e.raw is None else e.raw.replace('"', '“')}">{e.date}''')
                res.append(f'''<span onclick="__runShellCommand('generic', '{e.date}')">📈</span>''')
                res.append(f'''<span onclick="__runShellCommand('smooth', '{e.date}')">⛰️</span>''')
                res.append(f'''<span onclick="__runShellCommand('gpxsee', '{e.date}')">🏔️</span>''')
                res.append('</td>')
                res.append(f'<td class="graded dist" style="{st_dist}" title="{"{:2.2f}".format(e.dist / (e.dur or 1e9) * 60)} km/h">{e.dist}{_sp}km</td>')
                res.append(f'<td class="graded dur" style="{st_dur}">{duration(int(e.dur or 0))}</td>')
                res.append(f'<td class="graded d_pos" style="{st_d_pos}" title="{"{:2.2f}".format((e.dist+(e.d_pos or 0)/150) / (e.dur or 1e9) * 60)} 🔥/h">{e.d_pos or 0}{_sp}D+</td>')
            res.append('</tr>')

        res.append('</tbody></table>')
        res.append(style_table)
        return res


    class Executor(anywidget.AnyWidget):
        ex = traitlets.List([]).tag(sync=True)
        @traitlets.observe("ex")
        def _observe_ex(self, change):
            print(change)
            if change['new'] != []:
                self.ex = ''
                runShellCommand(*change['new'])

        _esm = """
        function render({ model, el }) {
            globalThis.__runShellCommand = (a, b) => {
                model.set('ex', [a, b])
                model.save_changes()
            }
        }
        export default { render };
        """
        _css = """"""

    ui_executor = mo.ui.anywidget(Executor())
    class InnerHTML(anywidget.AnyWidget):
        content = traitlets.Unicode('')
        def __init__(self, content):
            self.content = content
        _esm = """
        function render({ model, el }) {
            el.innerHTML = model.get('content')
        }
        export default { render };
        """

    ui_weekly = mo.ui.anywidget(InnerHTML("\n".join(_ui_weekly(entries, limit=50 if showOnlyRecent.value else 1e10))))
    #ui_weekly = mo.Html("\n".join(_ui_weekly(entries, limit=50 if showOnlyRecent.value else 1e10)))
    return (
        Executor,
        InnerHTML,
        colorbar_scale,
        duration,
        entries_in_week,
        ui_executor,
        ui_weekly,
    )


@app.cell
def __(
    colorbar_scale,
    duration,
    max_monthly_stats,
    max_shoely_stats,
    max_yearly_stats,
    mo,
    monthly_stats,
    shoely_stats,
    style_table,
    yearly_stats,
):
    def _ui_stats(stats, max_stats):
        res = []
        res.append('<table><tbody>')
        m = max_stats
        for i,m in enumerate(stats):
            res.append('<tr>')
            dist = m[1]['dist']
            dur = m[1]['dur']
            d_pos = m[1]['d_pos']
            d_neg = m[1]['d_neg']
            st_dist = "--v: " + str(colorbar_scale(dist, 30, max_stats['dist']))
            st_dur = "--v: " + str(colorbar_scale(dur, 300, max_stats['dur']))
            st_d_pos = "--v: " + str(colorbar_scale(d_pos, 1000, max_stats['d_pos']))
            res.append(f'<td>{m[0]}</td>')
            res.append(f'<td class="graded dist" style="{st_dist}">{dist} km</td>')
            res.append(f'<td class="graded dur" style="{st_dur}">{duration(dur)}</td>')
            res.append(f'<td class="graded d_pos" style="{st_d_pos}">{d_pos} D+</td>')
            res.append(f'<td>{d_neg} D-</td>')
            res.append('</tr>')

        res.append('</tbody></table>')
        res.append(style_table)
        return res

    ui_monthly = mo.Html("\n".join(_ui_stats(monthly_stats, max_monthly_stats)))
    ui_yearly = mo.Html("\n".join(_ui_stats(yearly_stats, max_yearly_stats)))
    ui_shoely = mo.Html("\n".join(_ui_stats(shoely_stats, max_shoely_stats)))
    return ui_monthly, ui_shoely, ui_yearly


@app.cell
def __(live):
    import numpy as np
    import collections
    import subprocess
    import random
    from pathlib import Path

    ld = live.import_all('logdown')
    #import logdown as ld
    return Path, collections, ld, np, random, subprocess


@app.cell
def __(colorbar_scale, np):
    def _():
        import matplotlib.pyplot as plt
        x = np.arange(0,10000,10)
        plt.plot(x, colorbar_scale(x, 1500, 10000))
        plt.show()
    #_()
    return


@app.cell
def __(colorbar_scale, entries, np):
    def _():
        import matplotlib.pyplot as plt
        for what in 'd_pos dist dur'.split(' '):
            data = [e[what] for e in entries if e[what] is not None]
            plt.hist(data, bins=100)
            plt.vlines([np.mean(data), np.median(data), np.mean(data)+np.std(data)*1], 0, 200, 'red')
            plt.title(what)
            plt.show()
            if what == 'd_pos':
                plt.hist(colorbar_scale(np.array(data), 1000, np.max(data)), bins=100)
            if what == 'dist':
                plt.hist(colorbar_scale(np.array(data), 30, np.max(data)), bins=100)
            if what == 'dur':
                plt.hist(colorbar_scale(np.array(data), 300, np.max(data)), bins=100)
            plt.show()

    #_()
    return


@app.cell
def __(collections, np):
    def aggregate(entries, agg=np.sum):
        return {
            'dist': int(agg([e['dist'] for e in entries])),
            'd_pos': int(agg([e['d_pos'] for e in entries if e['d_pos'] is not None])),
            'd_neg': int(agg([e['d_neg'] for e in entries if e['d_neg'] is not None])),
            'dur': int(agg([e['dur'] for e in entries if e['dur'] is not None])),
        }

    def pairs_to_dict(l):
        return {k:v for (k,v) in l}

    def max0(a):
        if len(a) == 0: return 0
        else: return np.max(a)

    def namedtuple_dict(d, typename='new'):
        top = collections.namedtuple(typename, [i for i,j in d.items() if not i.startswith('_')])(*[j for i,j in d.items() if not i.startswith('_')])
        return top
    return aggregate, max0, namedtuple_dict, pairs_to_dict


@app.cell
def __(Path):
    #path = 'example-journal.md'
    path = '/home/twilight/doc/notes/divers/course-journal.md'
    gpx_cwd = str(Path.home()) + '/doc/notes/gpx'
    return gpx_cwd, path


@app.cell
def __(ld, path, refreshOnLoadSeq):
    print(refreshOnLoadSeq())
    #entries = []

    #def _reloadLogfile(entries):
    #    entries[:] = []
    try:
        entries = list(reversed([vars(e) for e in ld.parse_logdown(path)]))
    except:
        pass

    #_reloadLogfile(entries)
    return entries,


@app.cell
def __(aggregate, entries, namedtuple_dict):
    total = namedtuple_dict(aggregate(entries))
    return total,


@app.cell
def __(aggregate, entries):
    def computed_weekly_stats(entries):
        weeks = list(reversed(sorted(list(set((e['week'] for e in entries))))))
        groups = { w: [] for w in weeks }
        for e in entries:
            groups[e['week']].append(e)
        res = [(w, aggregate(groups[w])) for w in weeks]
        return res

    weekly_stats = computed_weekly_stats(entries)
    return computed_weekly_stats, weekly_stats


@app.cell
def __(aggregate, entries):
    def computed_monthly_stats(entries):
        months = list(reversed(sorted(list(set((e['month'] for e in entries))))))
        groups = { m: [] for m in months }
        for e in entries:
            groups[e['month']].append(e)
        res = [(m, aggregate(groups[m])) for m in months]
        return res

    monthly_stats = computed_monthly_stats(entries)
    return computed_monthly_stats, monthly_stats


@app.cell
def __(aggregate, entries):
    def computed_yearly_stats(entries):
        years = list(sorted(list(set((e['date'][:4] for e in entries))), reverse=True))
        groups = { m: [] for m in years }
        for e in entries:
            groups[e['date'][:4]].append(e)
        res = [(m, aggregate(groups[m])) for m in years]
        return res

    yearly_stats = computed_yearly_stats(entries)
    return computed_yearly_stats, yearly_stats


@app.cell
def __(aggregate, entries):
    def computed_shoely_stats(entries):
        shoes = list(set((e['shoes'] for e in entries)))
        groups = { m: [] for m in shoes }
        for e in entries:
            groups[e['shoes']].append(e)
        shoes = sorted(shoes, key=lambda s: groups[s][0]['date'], reverse=True)
        res = [(m, aggregate(groups[m])) for m in shoes]
        return res

    shoely_stats = computed_shoely_stats(entries)
    return computed_shoely_stats, shoely_stats


@app.cell
def __(
    aggregate,
    entries,
    max0,
    monthly_stats,
    pairs_to_dict,
    shoely_stats,
    weekly_stats,
    yearly_stats,
):
    weekly_stats_dict = pairs_to_dict(weekly_stats)
    monthly_stats_dict = pairs_to_dict(monthly_stats)
    yearly_stats_dict = pairs_to_dict(yearly_stats)
    shoely_stats_dict = pairs_to_dict(shoely_stats)

    max_daily_stats = aggregate(entries, agg=max0)
    max_weekly_stats = aggregate([t[1] for t in weekly_stats], agg=max0)
    max_monthly_stats = aggregate([t[1] for t in monthly_stats], agg=max0)
    max_yearly_stats = aggregate([t[1] for t in yearly_stats], agg=max0)
    max_shoely_stats = aggregate([t[1] for t in shoely_stats], agg=max0)
    return (
        max_daily_stats,
        max_monthly_stats,
        max_shoely_stats,
        max_weekly_stats,
        max_yearly_stats,
        monthly_stats_dict,
        shoely_stats_dict,
        weekly_stats_dict,
        yearly_stats_dict,
    )


@app.cell
def __(max_weekly_stats):
    max_weekly_stats
    return


@app.cell
def __(gpx_cwd, path, subprocess):
    import asyncio

    #async
    def doCall(what, e, cwd, *cmd):
        subprocess.Popen(' '.join(cmd), shell=True)
        return
        #if e is None:
        #    e = {'date': 'global'}
        #r = {
        #    'id': what+'--'+e['date']+'--'+str(random.random()),
        #    'text': what+'('+e['date']+')',
        #}
        ##self.currentlyRunning.append(r)
        #proc = await asyncio.create_subprocess_shell(' '.join(cmd))
        #await asyncio.wait_for(proc.wait(), timeout=None)
        ##self.currentlyRunning.remove(r)



    def runShellCommand(what, e=None):
        cwd = gpx_cwd
        #go = lambda *cmd: asyncio.ensure_future(doCall(what, e, cwd, 'cd', cwd, '&&', *cmd))
        go = lambda *cmd: doCall(what, e, cwd, 'cd', cwd, '&&', *cmd)
        if what == 'generic':
            go('./generic.sh', str(e)+'*.gpx', 'vel=ddist', 'shouldwait=false')
        elif what == 'smooth':
            go('python3', '$HOME/projects/trail-tools/to-import/gpxlib.py', str(e)+'*.gpx', 'old', 'fast')
        elif what == 'gpxsee':
            go('gpxsee', str(e)+'*.gpx')
        elif what == 'edit-logs':
            go('emacs', path)
        elif what == 'edit-races':
            go('libreoffice', '$HOME/projects/nextcloud-mycorecnrs/random/carnet-courses.xlsx')
        elif what == 'edit-parcourstest':
            go('libreoffice', '$HOME/projects/nextcloud-mycorecnrs/random/TrainimmXT.xlsx')
        elif what == 'edit-notes':
            import re
            go('emacs', re.sub(r'[.]md$', r'-notes.md', path))
    return asyncio, doCall, runShellCommand


@app.cell
def __():
    import anywidget
    import traitlets
    return anywidget, traitlets


@app.cell
def __(anywidget, mo, traitlets):
    class OnClick(anywidget.AnyWidget):
        content = traitlets.Unicode('')
        click = traitlets.Bool(False).tag(sync=True)

        @traitlets.observe("click")
        def _observe_click(self, change):
            if change['new']:
                self.click = False
                self.cb()

        def __init__(self, cb, content):
            self.cb = cb
            self.content = content

        _esm = """
        function render({ model, el }) {
            el.innerHTML = model.get('content')
            el.addEventListener('click', () => {
                console.log(globalThis)
                model.set('click', true)
                model.save_changes()
            })
        }
        export default { render };
        """
        _css = """"""

    def onclick(cb, content):
        return mo.ui.anywidget(OnClick(cb, content))
    return OnClick, onclick


@app.cell
def __(onclick):
    widget = onclick(lambda: print("OK"), 'Hello<b>wiii</b>')
    widget
    return widget,


@app.cell
def __(lrefresh):
    lrefresh
    return


@app.cell
def __(live):
    import sys
    _GPXPATH = '/home/twilight/doc/notes/gpx'
    sys.path.append(_GPXPATH)
    gpxplot = live.import_all('gpxplot')
    df = gpxplot.process(["DUMMY", "-n", "9000", "-m", "ele", _GPXPATH+"/2024-07-04_12-11-01_2024-07-04_12-11-01.gpx"])
    df.columns
    return df, gpxplot, sys


@app.cell
def __(mo):
    lgetalt, lsetalt = mo.state(0)
    barriers = []
    return barriers, lgetalt, lsetalt


@app.cell
def __(barriers, df, lgetalt, mo):
    mo.stop(True)

    #import altair as alt
    import plotly.express as px
    #import seaborn as sns
    #import matplotlib.pyplot as plt

    _x = 'dist'
    _df = df.melt([_x, 'ddist'], value_vars=['ele', 'sele', 'dplus', 'dmoins'])

    print(_df)

    #_chart = sns.relplot(
    #    data=_df, kind="line",
    #    x=_x, y="value", hue="variable",
    #)
    #mo.mpl.interactive(plt.gcf())

    print(lgetalt())
    _chart = px.line(_df, x=_x, y='value', color="variable")
    _chart.add_selection(    x0=2.5, y0=6.5, x1=3.5, y1=5.5)
    for b in barriers:
        _chart = _chart.add_vline(b)
    achart = mo.ui.plotly(_chart, dict(modeBarButtonsToAdd=['drawline'], modeBarButtonsToRemove=['zoom2d']), on_change=print)

    # Create an Altair chart
    #lgetalt()
    #_chart = alt.Chart(_df).mark_line().encode(
    #    x=_x,
    #    y='value',
    #    color="variable",
    #).add_params(alt.selection_point(encodings=['x']))
    #achart = mo.ui.altair_chart(_chart | _chart.encode(x='ddist'))
    return achart, b, px


@app.cell
def __(achart, mo):
    mo.vstack([achart]) #, achart.value, achart.ranges, barriers])
    return


@app.cell
def __(achart, barriers, lsetalt, mo):
    mo.stop(True)
    if len(achart.ranges) > 0:
        _l, _r = achart.ranges['x']
        for _b in barriers:
            if _l < _b < _r:
                barriers.remove(_b)
                break
        else:
            if _l not in barriers:
                barriers.append(_l)
        barriers.sort()
        lsetalt(lambda i:i+1 )
    return


@app.cell
def __():
    #if len(achart.value) > 0:
    #    df['dist', 1000] = 20+random.randrange(20)
    #    lsetalt(lambda i:i+1 )
    return


@app.cell
def __():
    return


@app.cell
def __(achart):
    achart.value
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
