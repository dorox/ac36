from tornado.ioloop import IOLoop
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.directory import DirectoryHandler


io_loop = IOLoop.current()
dh = DirectoryHandler(filename="./stats_app")
app_stat = Application(dh)
dh = DirectoryHandler(filename="./map")
app_map = Application(dh)
server = Server(
    applications={"/stats_app": app_stat, "/map": app_map},
    io_loop=io_loop,
    address="0.0.0.0",
    port=5002,
    allow_websocket_origin=["*"],
)
server.start()
# server.show("/map")
io_loop.start()