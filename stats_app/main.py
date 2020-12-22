import os
import json
import pickle

import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Select, Span, CheckboxGroup
from bokeh.plotting import figure

stats = {
    "heading": "headingIntep",
    "heel": "heelInterp",
    "pitch": "pitchInterp",
    "speed": "speedInterp",
    "tws": "twsInterp",
    "twd": "twdInterp",
    "port foil": "leftFoilPosition",
    "stbd foil": "rightFoilPosition",
    "both foils": "both foils",
    "vmg": "vmg",
    "twa": "twa",
    "twa_abs": "twa_abs",
}
units = {
    "heading": "deg",
    "heel": "deg",
    "pitch": "deg",
    "speed": "kn",
    "tws": "kn",
    "twd": "deg",
    "port foil": "deg",
    "stbd foil": "deg",
    "both foils": "deg",
    "vmg": "kn",
    "twa": "deg(-180:180)",
    "twa_abs": "deg(0:180)",
}
cb_labels = ["Show race legs"]


def read_races():
    races = dict()
    for i in os.listdir("ACWS/"):
        with open(f"ACWS/{i}/stats.bin", "rb") as f:
            races[str(i)] = pickle.load(f)
    return races


def read_boats(race):
    path = f"ACWS/{race}/"
    with open(path + "boat1.bin", "rb") as f:
        boat1 = pickle.load(f)
    with open(path + "boat2.bin", "rb") as f:
        boat2 = pickle.load(f)
    return boat1, boat2


def get_twa(boat):
    twd = stat("twd", boat)
    cog = stat("heading", boat)
    x = cog["x"]
    twd = np.interp(x, twd["x"], twd["y"])
    cog = cog["y"]
    y = twd - cog
    y[y < 0] += 360
    y[y > 180] -= 360
    return dict(x=x, y=y)


def get_twa_abs(boat):
    d = get_twa(boat)
    x = np.abs(d["x"])
    y = np.abs(d["y"])
    return dict(x=x, y=y)


def get_vmg(boat):
    twa = get_twa_abs(boat)
    sog = stat("speed", boat)
    x = twa["x"]
    sog = np.interp(x, sog["x"], sog["y"])
    twa = twa["y"]
    y = np.abs(np.cos(np.deg2rad(twa)) * sog)
    return dict(x=x, y=y)


def get_both_foils(boat):
    stbd = stat("stbd foil", boat)
    port = stat("port foil", boat)
    x = np.concatenate((stbd["x"], port["x"]))
    y = np.concatenate((stbd["y"], port["y"]))
    return dict(x=x, y=y)


funcs = {
    "vmg": get_vmg,
    "twa": get_twa,
    "twa_abs": get_twa_abs,
    "both foils": get_both_foils,
}


def get_datetime(dic, boat):
    race_start = boat["legInterp"]["valHistory"][1][1]
    x = dic["x"]
    x = np.array(x - race_start, dtype="timedelta64[s]")
    return dict(x=x, y=dic["y"])


def stat(key, boat):
    if key in funcs:
        return funcs[key](boat)
    unit = 1
    if key == "tws":
        unit = 1.94384
    s = boat[stats[key]]["valHistory"]
    s = np.array(s)
    x = s[:, 1]
    y = s[:, 0] * unit
    return dict(x=x, y=y)


def get_boat_info(b, r, races):
    if str(b["teamId"]) == races[r]["LegStats"][0]["Boat"][0]["TeamID"]:
        c = races[r]["LegStats"][0]["Boat"][0]["TeamColour"]
        n = races[r]["LegStats"][0]["Boat"][0]["Country"]
    else:
        c = races[r]["LegStats"][0]["Boat"][1]["TeamColour"]
        n = races[r]["LegStats"][0]["Boat"][1]["Country"]
    return c, n


opts = sorted(read_races().keys(), key=int)
races_select = Select(value="1", title="Race", options=opts)
stats_select = Select(value="speed", title="Statistics", options=list(stats.keys()))
legs_cb = CheckboxGroup(labels=cb_labels)


def get_plot():
    r = races_select.value
    s = stats_select.value
    races = read_races()
    b1, b2 = read_boats(r)

    plot = figure(sizing_mode="stretch_width", x_axis_type="datetime", plot_height=500)
    plot.xaxis.axis_label = "Race time (start at 1/01)"
    plot.yaxis.axis_label = units[s]
    for b in (b1, b2):
        time_data = get_datetime(stat(s, b), b)
        b_src = ColumnDataSource(data=time_data)
        clr, name = get_boat_info(b, r, races)
        plot.line("x", "y", source=b_src, color=clr, legend_label=name)
        if cb_labels.index("Show race legs") in legs_cb.active:
            race_start = b["legInterp"]["valHistory"][1][1]
            for i in b["legInterp"]["valHistory"]:
                span = Span(
                    location=np.timedelta64(int(i[1] - race_start), "s"),
                    dimension="height",
                    line_color=clr,
                    line_alpha=0.3,
                    line_dash="dashed",
                    line_width=5,
                )
                plot.add_layout(span)
    return plot


def upd_plot(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()


def upd_stat(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()


races_select.on_change("value", upd_plot)
stats_select.on_change("value", upd_stat)
legs_cb.on_click(lambda a: upd_plot(a, "", ""))

controls = row(races_select, stats_select, legs_cb)

curdoc().add_root(column(get_plot(), controls, sizing_mode="stretch_both"))
curdoc().title = "stats"