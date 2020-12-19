import os
import json

import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select
from bokeh.plotting import figure

races = dict()
stats = {"heading":"headingIntep", "heel":"heelInterp", "pitch":"pitchInterp", "speed":"speedInterp", "tws":"twsInterp", "port foil": "leftFoilPosition", "stbd foil": "rightFoilPosition"}

for i in os.listdir('ACWS/'):
    with open(f'ACWS/{i}/stats.json') as f:
        races[str(i)] = json.load(f)

def read_boats(race):
    path = f'ACWS/{race}/'
    with open(path+"boat1.json") as f:
        boat1 = json.load(f)
    with open(path+"boat2.json") as f:
        boat2 = json.load(f)
    return boat1, boat2

def stat(key, boat):
    s = boat[stats[key]]['valHistory']
    s = np.array(s)
    x = s[:,1]
    y = s[:,0]
    return dict(x=x, y=y)

def get_boat_info(b, r):
    if str(b['teamId']) == races[r]['LegStats'][0]['Boat'][0]['TeamID']:
        c = races[r]['LegStats'][0]['Boat'][0]['TeamColour']
        n = races[r]['LegStats'][0]['Boat'][0]['Country']
    else:
        c = races[r]['LegStats'][0]['Boat'][1]['TeamColour']
        n = races[r]['LegStats'][0]['Boat'][1]['Country']
    return c, n

b1_src = ColumnDataSource(data = dict(x=[], y=[]))
b2_src = ColumnDataSource(data = dict(x=[], y=[]))

races_select = Select(value="1", title='Race', options=sorted(races.keys()))
stats_select = Select(value="speed", title="Statistics", options=list(stats.keys()))

def get_plot():
    r=races_select.value
    s=stats_select.value
    plot = figure(plot_width=900)
    b1, b2 = read_boats(r)
    c1, n1 = get_boat_info(b1, r)
    c2, n2 = get_boat_info(b2, r)
    plot.line('x', 'y', source=b1_src, color=c1, legend_label=n1)
    plot.line('x', 'y', source=b2_src, color=c2, legend_label=n2)
    b1_src.data = stat(s, b1)
    b2_src.data = stat(s, b2)
    return plot

def upd_plot(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()

def upd_stat(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()

races_select.on_change('value', upd_plot)
stats_select.on_change('value', upd_stat)

controls = row(races_select, stats_select)

curdoc().add_root(column(get_plot(), controls))
curdoc().title = "stats"
