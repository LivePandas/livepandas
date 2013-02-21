import json
import threading
import tornado.ioloop
import tornado.web
import tornado.websocket


class StaticHandler(tornado.web.RequestHandler):
    def initialize(self, static):
        self.static = static

    def get(self):
        self.write(self.static)                


class FunctionHandler(tornado.web.RequestHandler):
    def initialize(self, func):
        self.func = func

    def get(self):        
        try:
            kwargs = json.loads(self.get_argument('kwargs', '{}'))
            data = {'result': self.func(**kwargs)}
        except Exception, e:
            data = {'exception': str(e)}
            self.set_status(400)
            
        self.write(json.dumps(data))

class FunctionWebSocketHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, func):
        self.func = func
    
    def on_message(self, message):
        print message
        try:
            kwargs = json.loads(message)
            data = {'result': self.func(**kwargs)}
        except Exception, e:
            data = {'exception': str(e)}
            
        self.write_message(json.dumps(data))

    def open(self):
        print "WebSocket opened"

    def on_close(self):
        print "WebSocket closed"


class LocalServer(threading.Thread):

    def __init__(self, html=None, python=None, port=8888):
        threading.Thread.__init__(self)

        self.port = port

        # Create the application.
        print(" * Creating Tornado application.")

        self.handlers = []
        if html != None:

            print(" * Add html handler.")
            self.handlers.append((r'/', StaticHandler, {'static': html}))

        # Add python code if needed.
        if python is not None:
            self.add_python(python)

        application = tornado.web.Application(self.handlers)

        # Start listening.
        application.listen(self.port)

        # IO Loop instance.
        self.ioloop = tornado.ioloop.IOLoop.instance()

    def add_python(self, code):
        " Add the python functions. "

        ns = {}
        exec compile(code, '<string>', 'exec') in ns

        # Check for the registered.
        functions = [(k, v) for k, v in ns.items() if k.startswith('livepandas_') and callable(v)]

        # Define one handler per function.
        for name, func in functions:

            path = r"/" + name.replace('livepandas_', '')

            print(" * Adding http handler at 'http://localhost:%d%s'" % (
                self.port, path, ))
            print(" * Adding websocket handler at 'ws://localhost:%d%s/ws'" % (
                self.port, path, ))

            self.handlers.append((path , FunctionHandler, {'func': func}))
            self.handlers.append((path + "/ws" , FunctionWebSocketHandler, {'func': func}))

    def run(self):
        print(" * Local server started. Hit Ctrl-C to stop it.")
        self.ioloop.start()

    def stop(self):
        print(" * Chao!")
        self.ioloop.stop()
