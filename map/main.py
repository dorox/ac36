import pickle
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider, Span, Select
from bokeh.models.callbacks import CustomJS
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider

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
    "both foils": "both foils",
    "vmg": "vmg",
    "twa": "twa",
    "twa_abs": "twa_abs",
    "vmg/tws": "tws/vmg",
}


def get_b(n):
    with open(f"map/boats.bin", "rb") as f:
        b1 = pickle.load(f)
        b2 = pickle.load(f)
    b = (b1, b2)[n - 1]
    return b


# position is supplied in web mercator coordinates
map = figure(
    x_range=(1.945e7, 1.947e7),
    y_range=(-4.420e6, -4.404e6),
    tools="pan, wheel_zoom, reset",
    active_scroll="wheel_zoom",
    sizing_mode="stretch_both",
)
map.axis.visible = False
map.add_tile(get_provider(CARTODBPOSITRON))

plot = figure(
    x_axis_type="datetime",
    tools="pan, xwheel_zoom, reset, box_zoom",
    sizing_mode="stretch_width",
    active_scroll="xwheel_zoom",
)
stats_select = Select(value="speed", title="Statistics", options=list(stats.keys()))


def add_boat(b, map):
    track = ColumnDataSource(
        data={
            "lon": b["lon"],
            "lat": b["lat"],
            "hdg": -b["heading"],
        }
    )
    pos = ColumnDataSource(
        data={
            "lon": [b["lon"][0]],
            "lat": [b["lat"][0]],
            "hdg": [-b["heading"][0]],
            "url": ["map/static/boat.png"],
        }
    )
    map.image_url(
        url="url",
        x="lon",
        y="lat",
        angle="hdg",
        w=8,
        h=23,
        anchor="center",
        angle_units="deg",
        source=pos,
    )
    map.line(x="lon", y="lat", color=b["color"], source=track)

    boat_data = ColumnDataSource(
        data={"lon": b["lon"], "lat": b["lat"], "hdg": -b["heading"]}
    )
    cb_pos = CustomJS(
        args=dict(track=track, pos=pos, b=boat_data),
        code="""
        // console.log('cb_pos')
        var n = cb_obj.value
        var b = b.data
        track.data = {
            lon: b['lon'].slice(n-Math.min(n, 800), n+1),
            lat: b['lat'].slice(n-Math.min(n, 800), n+1)
        };
        pos.data.lon = [b['lon'][n]];
        pos.data.lat = [b['lat'][n]];
        pos.data.hdg = [b['hdg'][n]];
        pos.change.emit()
        track.change.emit()
        """,
    )

    b["cb_pos"] = cb_pos
    return pos


def add_boat_plot(b, plot):
    s = "speed"
    b_stats = ColumnDataSource(data={k: b[k] for k, v in stats.items()})
    cds_b = ColumnDataSource(data={"time": b["x"], "y": b[s]})
    plot.line(
        "time",
        "y",
        source=cds_b,
        color=b["color"],
        legend_label=b["name"],
        name=b["name"],
    )
    cb_js_stat = CustomJS(
        args=dict(b_stats=b_stats, cds_b=cds_b),
        code="""
        var s = b_stats.data[cb_obj.value]
        cds_b.data['y'] = s
        cds_b.change.emit()
    """,
    )
    stats_select.js_on_change("value", cb_js_stat)


b1 = get_b(1)
b2 = get_b(2)
for b in (b1, b2):
    b["CDS_pos"] = add_boat(b, map)
    add_boat_plot(b, plot)

cb_range = CustomJS(
    args=dict(b1=b1["CDS_pos"], b2=b2["CDS_pos"], p=map),
    code="""
    var x1 = b1.data.lon[0]
    var y1 = b1.data.lat[0]
    var x2 = b2.data.lon[0]
    var y2 = b2.data.lat[0]
    var rx = (p.x_range.end - p.x_range.start) / 2
    var ry = (p.y_range.end - p.y_range.start) / 2
    var x = (x1 + x2) / 2;
    var y = (y1 + y2) / 2;
    p.x_range.start = Math.min(x - rx, x1, x2)
    p.x_range.end = Math.max(x + rx, x1, x2)
    p.y_range.start = Math.min(y - ry, y1, y2)
    p.y_range.end = Math.max(y + ry, y1,y2)
    // console.log('cb_range')
    """,
)

cds_span = ColumnDataSource(data={"times": b1["x"]})

sp_time = Span(location=0, dimension="height", line_color="grey", line_width=1)
plot.add_layout(sp_time)
cb_sp_time = CustomJS(
    args=dict(sp=sp_time, cds=cds_span),
    code="""
    // console.log('sp_time')
    var n = cb_obj.value
    sp.location = cds.data.times[n]
    """,
)

sl = Slider(
    start=0,
    end=len(b1["heading"]) - 1,
    value=0,
    step=1,
    title="Time",
    sizing_mode="stretch_width",
)

sl.js_on_change("value", b1["cb_pos"], b2["cb_pos"])
sl.js_on_change("value", cb_range)
sl.js_on_change("value", cb_sp_time)


curdoc().add_root(column(map, plot, row(sl, stats_select), sizing_mode="stretch_width"))
