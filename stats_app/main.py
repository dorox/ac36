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

import ac36data


stats = {
    "heading": "headingIntep",
    "heel": "heelInterp",
    "pitch": "pitchInterp",
    "height": "elevInterp",
    "speed": "speedInterp",
    "tws": "twsInterp",
    "twd": "twdInterp",
    "port foil": "leftFoilPosition",
    "stbd foil": "rightFoilPosition",
    # "both foils": "both foils",
    "vmg": "vmg",
    "cvmg": "cvmg",
    "twa": "twa",
    "twa_abs": "twa_abs",
    "vmg/tws": "tws/vmg",
}
units = {
    "heading": "deg",
    "heel": "deg",
    "pitch": "deg",
    "height": "m",
    "speed": "kn",
    "tws": "kn",
    "twd": "deg",
    "port foil": "deg",
    "stbd foil": "deg",
    "both foils": "deg",
    "vmg": "kn",
    "cvmg": "kn",
    "twa": "deg(-180:180)",
    "twa_abs": "deg(0:180)",
    "vmg/tws": "vmg/tws",
}

cb_labels = ["Show race legs"]


event_select = Select(value="prada2021", title="Event", options=ac36data.events)
opts = ac36data.get_races(event_select.value)
races_select = Select(value="1", title="Race", options=opts)
stats_select = Select(value="speed", title="Statistics", options=list(stats.keys()))
legs_cb = CheckboxGroup(labels=cb_labels)


def get_plot():
    e = event_select.value
    r = races_select.value
    s = stats_select.value
    b1, b2 = ac36data.get_boats(e, r)

    plot = figure(
        sizing_mode="stretch_width",
        x_axis_type="datetime",
        plot_height=500,
        tools="pan, xwheel_zoom, reset, box_zoom",
    )
    plot.add_tools(
        HoverTool(
            tooltips=[
                ("boat", "$name"),
                (s, "@y"),
                ("time", "@time{%H:%M:%S}"),
            ],
            formatters={"@time": "datetime"},
        )
    )
    plot.xaxis.axis_label = "Time"
    plot.yaxis.axis_label = f"{s}, {units[s]}"

    def selection_change(attr, old, new):
        print(attr, old, new)

    for b in (b1, b2):
        time_data = {"time": b["x"], "y": b[s]}
        b_src = ColumnDataSource(data=time_data)
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
        for i in b["legs"]:
            span = Span(
                location=i,
                dimension="height",
                line_color=b["color"],
                line_alpha=0.3,
                line_dash="dashed",
                line_width=5,
            )
            plot.add_layout(span)


def upd_plot(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()


def upd_races_select(attr, old, new):
    races_select.options = ac36data.get_races(event_select.value)
    races_select.value = "1"


def upd_stat(attr, old, new):
    curdoc().roots[0].children[0] = get_plot()


event_select.on_change("value", upd_races_select)
event_select.on_change("value", upd_plot)
races_select.on_change("value", upd_plot)
stats_select.on_change("value", upd_stat)
legs_cb.on_click(lambda a: upd_plot(a, "", ""))

controls = row(event_select, races_select, stats_select, legs_cb)

curdoc().add_root(column(get_plot(), controls, sizing_mode="stretch_both"))
curdoc().title = "stats"