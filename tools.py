import numpy as np
import os
import pickle

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


def read_races():
    races = dict()
    if "ACWS" in os.listdir():
        path = "ACWS/"
    elif "data" in os.listdir():
        path = "data/"
    for i in os.listdir(path):
        with open(f"{path}{i}/stats.bin", "rb") as f:
            races[str(i)] = pickle.load(f)
    return races


def read_boats(race):
    if "ACWS" in os.listdir():
        path = f"ACWS/{race}/"
        with open(path + "boat1.bin", "rb") as f:
            boat1 = pickle.load(f)
        with open(path + "boat2.bin", "rb") as f:
            boat2 = pickle.load(f)
    elif "data" in os.listdir():
        path = "data/"
        with open(path + race + "/boats.bin", "rb") as f:
            boat1 = pickle.load(f)
            boat2 = pickle.load(f)
    else:
        raise Exception("folder not found")
    return boat1, boat2


def get_twa(boat):
    twd = stat("twd", boat)
    cog = stat("heading", boat)
    x = cog["x"]
    x = np.linspace(x[0], x[-1], int(x[-1] - x[0]))
    twd = np.interp(x, twd["x"], twd["y"])
    cog = np.interp(x, cog["x"], cog["y"])
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
    x = np.linspace(x[0], x[-1], len(x))
    sog = np.interp(x, sog["x"], sog["y"])
    twa = twa["y"]
    y = np.cos(np.deg2rad(twa)) * sog
    legs = boat["legInterp"]["valHistory"]
    for i, leg in enumerate(legs[1:], 1):
        if not leg[0] % 2 and i != len(legs) - 1:
            mask = np.logical_and(x < legs[i + 1][1], x > legs[i][1])
            y[mask] *= -1
    return dict(x=x, y=y)


def get_both_foils(boat):
    stbd = stat("stbd foil", boat)
    port = stat("port foil", boat)
    x = np.concatenate((stbd["x"], port["x"]))
    y = np.concatenate((stbd["y"], port["y"]))
    return dict(x=x, y=y)


def get_vmgtws(boat):
    vmg = get_vmg(boat)
    tws = stat("tws", boat)
    tws = np.interp(vmg["x"], tws["x"], tws["y"])
    return dict(x=vmg["x"], y=vmg["y"] / tws)


def get_datetime(dic, boat):
    race_start = boat["legInterp"]["valHistory"][1][1]
    x = dic["x"]
    x = np.array(x - race_start, dtype="timedelta64[s]")
    return dict(x=x, y=dic["y"])


funcs = {
    "vmg": get_vmg,
    "twa": get_twa,
    "twa_abs": get_twa_abs,
    "both foils": get_both_foils,
    "vmg/tws": get_vmgtws,
}


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


# ---USED FOR SAVING DATA INTO ARCHIVE---
# ---------------------------------------


def interpolate_boat(boat):
    keep = dict()
    x = stat("heading", boat)
    x = x["x"]
    x = np.linspace(int(x[0]), int(x[-1]), int(x[-1] - x[0]), dtype=int)
    for s in stats:
        data = tools.stat(s, boat)
        y = np.interp(x, data["x"], data["y"])
        keep[s] = y
    race_start = boat["legInterp"]["valHistory"][1][1]
    keep["legs"] = dict(boat["legInterp"]["valHistory"])
    keep["x"] = np.array(x - race_start, dtype="timedelta64[s]")
    return keep


def save_boats():
    path = "data/"
    races = read_races()
    for r in races:
        if r not in os.listdir(path):
            os.mkdir(path + r)
        b1, b2 = read_boats(r)
        with open(path + r + f"/boats.bin", "wb") as f:
            for b in b1, b2:
                data = interpolate_boat(b)
                color, name = get_boat_info(b, r, races)
                data["color"] = color
                data["name"] = name
                pickle.dump(data, f)


def save_stats():
    path = "data/"
    races = read_races()
    for r in races:
        with open(path + r + "/stats.bin", "wb") as f:
            pickle.dump(races[r], f)