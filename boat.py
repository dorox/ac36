import numpy as np
# import matplotlib.pyplot as plt
import json

def read_boat(path):
    with open(path) as f:
        boat = json.load(f)

    speed = boat['speedInterp']['valHistory']
    speed = np.array(speed)

    x = speed[:,1]
    y = speed[:,0]
    return x, y

x1, y1 = read_boat('ACWS/8/boat1.json')
x2, y2 = read_boat('ACWS/8/boat2.json')
plt.plot(x1,y1)
plt.plot(x2, y2)
plt.show()
