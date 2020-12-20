import os
import json

import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select
from bokeh.plotting import figure

stats = {"heading":"headingIntep", "heel":"heelInterp", "pitch":"pitchInterp", "speed":"speedInterp", "tws":"twsInterp", "twd":"twdInterp", "port foil": "leftFoilPosition", "stbd foil": "rightFoilPosition",
"vmg":"vmg",
"twa":"twa",
"twa_abs":"twa_abs"
}

def read_races():
    races = dict()
    for i in os.listdir('ACWS/'):
        with open(f'ACWS/{i}/stats.json') as f:
            # print(json.load(f))
            races[str(i)] = json.load(f)
    return races

def read_boats(race):
    path = f'ACWS/{race}/'
    with open(path+"boat1.json") as f:
        boat1 = json.load(f)
    with open(path+"boat2.json") as f:
        boat2 = json.load(f)
    return boat1, boat2

def get_twa(boat):
    twd = stat('twd', boat)
    cog = stat('heading', boat)
    x = cog['x']
    twd = np.interp(x, twd['x'], twd['y'])
    cog = cog['y']
    y = twd-cog
    y[y<0] += 360
    y[y>180] -=360
    return dict(x=x, y=y)

def get_twa_abs(boat):
    d = get_twa(boat)
    x = np.abs(d['x'])
    y = np.abs(d['y'])
    return dict(x=x, y=y)

def get_vmg(boat):
    twa = get_twa_abs(boat)
    sog = stat('speed', boat)
    x = twa['x']
    sog = np.interp(x, sog['x'], sog['y'])
    twa = twa['y']
    y = np.abs(np.cos(np.deg2rad(twa))*sog)
    return dict(x=x, y=y)

funcs = {"vmg":get_vmg, "twa":get_twa, "twa_abs":get_twa_abs}

def stat(key, boat):
    if key in funcs:
        return funcs[key](boat)
    s = boat[stats[key]]['valHistory']
    s = np.array(s)
    x = s[:,1]
    y = s[:,0]
    return dict(x=x, y=y)

def get_boat_info(b, r, races):
    if str(b['teamId']) == races[r]['LegStats'][0]['Boat'][0]['TeamID']:
        c = races[r]['LegStats'][0]['Boat'][0]['TeamColour']
        n = races[r]['LegStats'][0]['Boat'][0]['Country']
    else:
        c = races[r]['LegStats'][0]['Boat'][1]['TeamColour']
        n = races[r]['LegStats'][0]['Boat'][1]['Country']
    return c, n

opts = sorted(read_races().keys(), key=int)
races_select = Select(value="1", title='Race', options=opts)
stats_select = Select(value="speed", title="Statistics", options=list(stats.keys()))

def get_plot():
    r=races_select.value
    s=stats_select.value
    b1, b2 = read_boats(r)
    b1_src = ColumnDataSource(data = dict(x=[], y=[]))
    b2_src = ColumnDataSource(data = dict(x=[], y=[]))
    b1_src.data = stat(s, b1)
    b2_src.data = stat(s, b2)

    plot = figure(plot_width=900)
    races = read_races()
    c1, n1 = get_boat_info(b1, r, races)
    c2, n2 = get_boat_info(b2, r, races)
    plot.line('x', 'y', source=b1_src, color=c1, legend_label=n1)
    plot.line('x', 'y', source=b2_src, color=c2, legend_label=n2)
    return plot

def upd_plot(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()

def upd_stat(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()
    # takes too much memory
    # for b in boats.values():
    #     b["source"].data = stat(new, b["boat"])

races_select.on_change('value', upd_plot)
stats_select.on_change('value', upd_stat)

controls = row(races_select, stats_select)

curdoc().add_root(column(get_plot(), controls))
curdoc().title = "stats"
