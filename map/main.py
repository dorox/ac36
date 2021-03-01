from datetime import datetime
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import (
    ColumnDataSource,
    Slider,
    Span,
    Select,
    Toggle,
)
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
# --- Persistent data ----
boats = (dict(), dict())
videos = ColumnDataSource()

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
    width=100,
    options=list(opt_stats.keys()),
    name="stats",
)
sel_race = Select(
    value="17", title="Race", width=50, options=ac36data.get_races("prada2021")
)
sel_event = Select(
    value="prada2021", title="Event", width=100, options=["acws2020", "prada2021"]
)
sl_time = Slider(
    start=0,
    end=1,
    value=0,
    step=1,
    title="Time, ms",
    sizing_mode="stretch_width",
    name="time",
)
bt_play = Toggle(label="play", width=100, active=False)
cb_bt_play = CustomJS(
    args=dict(sl_time=sl_time),
    code="""
    //console.log('play')
    if (cb_obj.active) {
        cb_obj.label='pause'
        cb_obj.tags[0] = setInterval(function(){
            sl_time.value = sl_time.value+100
            }, 100)
        playerLeft.playVideo()
        playerMid.playVideo()
        playerRight.playVideo()
    } else {
        cb_obj.label='play'
        clearInterval(cb_obj.tags[0])
        playerLeft.pauseVideo()
        playerMid.pauseVideo()
        playerRight.pauseVideo()
    }
    """,
)

bt_play.js_on_click(cb_bt_play)


curdoc().add_root(column(map, plot, sizing_mode="stretch_both", name="figures"))
col = column(
    sl_time,
    row(bt_play, sel_stats, sel_event, sel_race),
    sizing_mode="stretch_both",
    name="col",
)
curdoc().add_root(col)


def get_cb_yt_seek(stats):
    offsets = {k: v["offset"] for k, v in stats["yt_videos"].items()}
    start_time = stats["course_info"]["startTime"] - 3 * 3600
    code = f"""
        console.log('yt_seek, {start_time}')
        var dt = cb_obj.value/1000 - {start_time}
        playerLeft.seekTo(dt + {offsets['PRT']})
        playerMid.seekTo(dt + {offsets['TV']})
        playerRight.seekTo(dt + {offsets['STBD']})
        """
    return CustomJS(code=code, name="cb_yt_seek")


def get_cb_yt_upd(stats):
    ids = {k: v["videoId"] for k, v in stats["yt_videos"].items()}
    code = f"""
        console.log('upd_yt');
        playerLeft.loadVideoById('{ids['PRT']}');
        playerLeft.playVideo()
        playerLeft.pauseVideo();
        playerMid.loadVideoById('{ids['TV']}');
        playerMid.playVideo()
        playerMid.pauseVideo();
        playerRight.loadVideoById('{ids['STBD']}');
        playerRight.playVideo()
        playerRight.pauseVideo();
        """
    return CustomJS(code=code, name="cb_yt_upd")


def get_boat_cds(boat, cds_id=None):
    if not cds_id:
        cds = ColumnDataSource()
    else:
        cds = curdoc().get_model_by_id(cds_id)
    cds.data = {k: v for k, v in boat.items() if type(v) != str and k != "legs"}
    cds.name = boat["name"]
    cds.tags = [boat["color"]]
    return cds


def add_boat_track(b_cds, boat):
    b = b_cds.data
    track = ColumnDataSource(
        data={
            "lon": b["lon"],
            "lat": b["lat"],
            "hdg": -b["heading"],
        },
        name="b_track",
    )
    boat["track"] = track.id
    pos = ColumnDataSource(
        data={
            "lon": [b["lon"][0]],
            "lat": [b["lat"][0]],
            "hdg": [-b["heading"][0]],
            "url": ["map/static/boatMH.png"],
        },
        name="b_pos",
    )
    boat["pos"] = pos.id
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
    line = map.line(
        x="lon", y="lat", color=b_cds.tags[0], source=track, name="line_track"
    )
    boat["line_track"] = line.id
    cb_pos = CustomJS(
        args=dict(track=track, pos=pos, b=b_cds),
        code="""
        // console.log('cb_pos')
        var n = cb_obj.value
        var b = b.data
        n = b.x.findIndex(x=>x>=n)
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


def add_boat_plot(b_cds, boat):
    stat = ColumnDataSource(
        data={"time": b_cds.data["x"], "y": b_cds.data["speed"]}, name="b_stat"
    )
    boat["stat"] = stat.id
    line = plot.line(
        "time",
        "y",
        source=stat,
        color=b_cds.tags[0],
        # legend_label=b_cds.name,
        name="line_stat",
    )
    boat["line_stat"] = line.id
    cb_js = CustomJS(
        args=dict(b=stat, b_cds=b_cds),
        code="""
        b.data.y = b_cds.data[cb_obj.value]
        b.change.emit()
        //console.log('stats_upd')
        """,
    )
    sel_stats.js_on_change("value", cb_js)


def add_boats():
    boats_raw = ac36data.get_boats(sel_event.value, sel_race.value)
    # sl_time.start = 0
    # sl_time.end = max((len(boats_raw[0]["x"]), len(boats_raw[1]["x"]))) - 1
    sl_time.start = max((boats_raw[0]["x"][0], boats_raw[1]["x"][0]))
    sl_time.end = min((boats_raw[0]["x"][-1], boats_raw[1]["x"][-1]))
    sl_time.step = boats_raw[0]["x"][2] - boats_raw[0]["x"][1]

    for b, d in zip(boats_raw, boats):
        cds = get_boat_cds(b)
        d["cds"] = cds.id
        add_boat_plot(cds, d)
        add_boat_track(cds, d)

    # --Vertical time indicator: ---
    sp_time = Span(location=0, dimension="height", line_color="grey", line_width=1)
    plot.add_layout(sp_time)

    cb_sp_time = CustomJS(
        args=dict(sp=sp_time, b=cds),
        code="""
        // console.log('sp_time')
        var n = cb_obj.value
        n = b.data.x.findIndex(x=>x>=n)
        sp.location = b.data.x[n]
        """,
    )
    sl_time.js_on_change("value", cb_sp_time)

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
    stats = ac36data.get_stats(sel_event.value, sel_race.value)
    sl_time.js_on_change("start", get_cb_yt_upd(stats))
    sl_time.js_on_change("value_throttled", get_cb_yt_seek(stats))


def upd_tracks(b_cds, boat):
    track = curdoc().get_model_by_id(boat["track"])
    pos = curdoc().get_model_by_id(boat["pos"])
    line = curdoc().get_model_by_id(boat["line_track"])
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


def upd_stats(b_cds, boat):
    stat = curdoc().get_model_by_id(boat["stat"])
    line = curdoc().get_model_by_id(boat["line_stat"])
    stat.data = {"time": b_cds.data["x"], "y": b_cds.data[sel_stats.value]}
    line.glyph.line_color = b_cds.tags[0]
    # # legends = plot.legend.items
    #     # legend.label["value"] = "hehe"


def upd_all(race=1):
    bt_play.active = False
    event = sel_event.value
    boats_raw = ac36data.get_boats(sel_event.value, race)
    stats = ac36data.get_stats(sel_event.value, race)
    for b, d in zip(boats_raw, boats):
        cds = get_boat_cds(b, d["cds"])
        upd_tracks(cds, d)
        upd_stats(cds, d)
    sl_time.js_property_callbacks["change:start"] = []
    sl_time.js_on_change("start", get_cb_yt_upd(stats))
    sl_time.start = max((boats_raw[0]["x"][0], boats_raw[1]["x"][0]))
    sl_time.end = min((boats_raw[0]["x"][-1], boats_raw[1]["x"][-1]))
    sl_time.step = boats_raw[0]["x"][2] - boats_raw[0]["x"][1]
    sl_time.value = sl_time.start
    sel_race.options = ac36data.get_races(event)
    sl_time.js_property_callbacks["change:value_throttled"] = []
    sl_time.js_on_change("value_throttled", get_cb_yt_seek(stats))


add_boats()
sel_race.on_change("value", lambda a, o, n: upd_all(race=n))
sel_event.on_change("value", lambda a, o, n: upd_all())
# upd_all(race=sel_race.value)
