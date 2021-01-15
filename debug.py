from tornado.ioloop import IOLoop
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.directory import DirectoryHandler


io_loop = IOLoop.current()
dh = DirectoryHandler(filename="./stats_app")
app = Application(dh)
server = Server(
    applications={"/stats_app": app},
    io_loop=io_loop,
    port=5001,
)
server.start()
server.show("/stats_app")
io_loop.start()