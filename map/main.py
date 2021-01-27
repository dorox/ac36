import pickle
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, Span, Select, LegendItem
from bokeh.models.callbacks import CustomJS
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider

import ac36data

opt_stats = {
    "heading": "headingIntep",
    "heel": "heelInterp",
    "pitch": "pitchInterp",
    "height": "elevInterp",
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


# position is supplied in web mercator coordinates
map = figure(
    x_range=(1.945e7, 1.947e7),
    y_range=(-4.420e6, -4.404e6),
    tools="pan, wheel_zoom, reset",
    active_scroll="wheel_zoom",
    sizing_mode="stretch_both",
    name="map",
)
map.axis.visible = False
map.add_tile(get_provider(CARTODBPOSITRON))

plot = figure(
    x_axis_type="datetime",
    tools="pan, xwheel_zoom, reset",
    sizing_mode="stretch_width",
    active_scroll="xwheel_zoom",
    height=200,
    name="figure",
)
sel_stats = Select(
    value="speed",
    title="Statistics",
    width=200,
    options=list(opt_stats.keys()),
    name="stats",
)
sel_race = Select(
    value="1", title="Race", width=50, options=ac36data.get_races("prada2021")
)
sl_time = Slider(
    start=0,
    end=1,
    value=0,
    step=1,
    title="Time",
    sizing_mode="stretch_width",
    name="time",
)

sel_race.on_change("value", lambda a, o, n: upd_all())

curdoc().add_root(
    column(map, plot, row(sl_time, sel_stats, sel_race), sizing_mode="stretch_width")
)

cds_boats = [
    ColumnDataSource(name="cds_boat"),
    ColumnDataSource(name="cds_boat"),
]


def get_boats(event="prada2021", race=1):
    boats = ac36data.get_boats(event, race)
    for cds, b in zip(cds_boats, boats):
        cds.data = {k: v for k, v in b.items() if type(v) != str}
        cds.name = b["name"]
        cds.tags = [b["color"]]


def add_boat_track(b_cds):
    b = b_cds.data
    track = ColumnDataSource(
        data={
            "lon": b["lon"],
            "lat": b["lat"],
            "hdg": -b["heading"],
        },
        name="b_track",
    )
    pos = ColumnDataSource(
        data={
            "lon": [b["lon"][0]],
            "lat": [b["lat"][0]],
            "hdg": [-b["heading"][0]],
            "url": ["map/static/boatMH.png"],
        },
        name="b_pos",
    )

    map.image_url(
        url="url",
        x="lon",
        y="lat",
        angle="hdg",
        w=12,
        h=23,
        anchor="center",
        angle_units="deg",
        source=pos,
        name="b_img",
    )
    map.line(x="lon", y="lat", color=b_cds.tags[0], source=track, name="line_track")

    cb_pos = CustomJS(
        args=dict(track=track, pos=pos, b=b_cds),
        code="""
        // console.log('cb_pos')
        b.change.emit()
        var n = cb_obj.value
        var b = b.data
        track.data = {
            lon: b['lon'].slice(n-Math.min(n, 200), n+1),
            lat: b['lat'].slice(n-Math.min(n, 200), n+1)
        };
        pos.data.lon = [b['lon'][n]];
        pos.data.lat = [b['lat'][n]];
        pos.data.hdg = [-b['heading'][n]];
        pos.change.emit()
        track.change.emit()
        """,
    )
    sl_time.js_on_change("value", cb_pos)


def add_boat_plot(b_cds):
    s = "speed"
    b = ColumnDataSource(
        data={"time": b_cds.data["x"], "y": b_cds.data[s]}, name="b_stat"
    )
    plot.line(
        "time",
        "y",
        source=b,
        color=b_cds.tags[0],
        # legend_label=b_cds.name,
        name="line_stat",
    )
    cb_js = CustomJS(
        args=dict(b=b, b_cds=b_cds),
        code="""
        b.data.y = b_cds.data[cb_obj.value]
        b.change.emit()
        //console.log('stats_upd')
        """,
    )
    sel_stats.js_on_change("value", cb_js)


def add_boats():
    get_boats()
    for b in cds_boats:
        add_boat_plot(b)
        add_boat_track(b)

    # --Vertical line to indicate time: ---
    sp_time = Span(location=0, dimension="height", line_color="grey", line_width=1)
    plot.add_layout(sp_time)
    cb_sp_time = CustomJS(
        args=dict(sp=sp_time, b=b),
        code="""
        // console.log('sp_time')
        var n = cb_obj.value
        sp.location = b.data.x[n]
        """,
    )
    sl_time.js_on_change("value", cb_sp_time)
    sl_time.end = len(b.data["x"]) - 1

    # -- Auto-centering ---
    b_pos = curdoc().select(dict(name="b_pos"))
    cb_range = CustomJS(
        args=dict(p=map, b1=b_pos[0], b2=b_pos[1]),
        code="""
        var x = (b1.data.lon[0] + b2.data.lon[0])/2
        var y = (b1.data.lat[0] + b2.data.lat[0])/2
        var rx = (p.x_range.end - p.x_range.start) / 2
        var ry = (p.y_range.end - p.y_range.start) / 2
        p.x_range.start = x - rx
        p.x_range.end = x + rx
        p.y_range.start = y - ry
        p.y_range.end = y + ry
        //console.log('cb_range')
        """,
    )

    sl_time.js_on_change("value", cb_range)


def upd_tracks():
    tracks = curdoc().select(dict(name="b_track"))
    positions = curdoc().select(dict(name="b_pos"))
    lines = curdoc().select(dict(name="line_track"))
    for track, pos, line, b_cds in zip(tracks, positions, lines, cds_boats):
        b = b_cds.data
        track.data = {
            "lon": b["lon"],
            "lat": b["lat"],
            "hdg": -b["heading"],
        }
        pos.data = {
            "lon": [b["lon"][0]],
            "lat": [b["lat"][0]],
            "hdg": [-b["heading"][0]],
            "url": ["map/static/boatMH.png"],
        }
        line.glyph.line_color = b_cds.tags[0]


def upd_stats():
    stats = curdoc().select(dict(name="b_stat"))
    lines = curdoc().select(dict(name="line_stat"))
    for stat, line, b in zip(stats, lines, cds_boats):
        stat.data = {"time": b.data["x"], "y": b.data[sel_stats.value]}
        line.glyph.line_color = b.tags[0]

    # # legends = plot.legend.items
    # for line, b in zip(lines, cds_boats):

    #     # legend.label["value"] = "hehe"


def upd_all():
    get_boats("prada2021", sel_race.value)
    upd_tracks()
    upd_stats()
    sl_time.end = len(cds_boats[0].data["x"]) - 1


add_boats()
