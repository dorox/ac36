import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    Select,
    Span,
    CheckboxGroup,
    HoverTool,
    BoxSelectTool,
)
from bokeh.plotting import figure

import tools


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
    "vmg/tws": "tws/vmg",
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
    "vmg/tws": "vmg/tws",
}

cb_labels = ["Show race legs"]


opts = sorted(tools.read_races().keys(), key=int)
races_select = Select(value="1", title="Race", options=opts)
stats_select = Select(value="speed", title="Statistics", options=list(stats.keys()))
legs_cb = CheckboxGroup(labels=cb_labels)


def get_plot():
    r = races_select.value
    s = stats_select.value
    # races = tools.read_races()
    b1, b2 = tools.read_boats(r)

    plot = figure(
        sizing_mode="stretch_width",
        x_axis_type="datetime",
        plot_height=500,
        tools="pan, xwheel_zoom, reset, box_zoom",
    )
    bs = BoxSelectTool(dimensions="width")
    plot.add_tools(
        HoverTool(
            tooltips=[
                ("boat", "$name"),
                ("speed", "@y"),
                ("time", "@time{%M:%S}"),
            ],
            formatters={"@time": "datetime"},
            mode="vline",
        ),
        bs,
    )
    plot.xaxis.axis_label = "Race time (start at 1/01)"
    plot.yaxis.axis_label = f"{s}, {units[s]}"

    def selection_change(attr, old, new):
        print(attr, old, new)

    for b in (b1, b2):
        time_data = {"time": b["x"], "y": b[s]}
        b_src = ColumnDataSource(data=time_data)
        b_src.selected.on_change("indices", selection_change)
        plot.line(
            "time",
            "y",
            source=b_src,
            color=b["color"],
            legend_label=b["name"],
            name=b["name"],
        )
        if cb_labels.index("Show race legs") in legs_cb.active:
            add_legs(plot, (b1, b2))
    plot.legend.click_policy = "hide"

    return plot


def add_legs(plot, boats):
    for b in boats:
        race_start = b["legs"][1]
        for i in b["legs"].values():
            span = Span(
                location=np.timedelta64(int(i - race_start), "s"),
                dimension="height",
                line_color=b["color"],
                line_alpha=0.3,
                line_dash="dashed",
                line_width=5,
            )
            plot.add_layout(span)


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