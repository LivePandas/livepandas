import argparse
import requests
import json
import time
import sys
import threading
import tornado.ioloop
import tornado.web

SERVER_BASE = 'http://livepandas.com'

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


class LocalServer(threading.Thread):

    def add_python(self, code):
        " Add the python functions. "

        ns = {}
        exec compile(code, '<string>', 'exec') in ns

        # Check for the registered.
        functions = [(k, v) for k, v in ns.items() if k.startswith('livepandas_') and callable(v)]

        # Define one handler per function.
        for name, func in functions:
            path = r"/" + name.replace('livepandas_', '')
            print " * Adding handler at '%s'" % (path, )
            self.handlers.append((path , FunctionHandler, {'func': func}))

    def __init__(self, html=None, code=None, port=8888):
        threading.Thread.__init__(self)

        # Create the application.
        print " * Creating Tornado application."
        self.handlers = []
        if html != None:
            print " * Add html handler."
            self.handlers.append((r'/', StaticHandler, {'static': html}))

        # Add python code if needed.
        if code is not None:
            self.add_python(code)

        application = tornado.web.Application(self.handlers)

        # Start listening.
        application.listen(port)

        # IO Loop instance.
        self.ioloop = tornado.ioloop.IOLoop.instance()

    def run(self):
        print " * Local server started. Hit Ctrl-C to stop it."
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()


def create_canvas(python_code, html_code=None):
    """ Create a canvas with the python and html code."""

    headers = {'Content-Type': 'application/json'}
    
    # Create an anonymous canvas (will be deleted after 5 minutes of the last usage)
    response = requests.post(SERVER_BASE + '/api/v1/canvases/', 
                             json.dumps({'python': python_code, 'author': None}),
                             headers=headers)
    
    if response.status_code != 201:
        raise Exception("API error creating the Canvas.")
        
    # Canvas created.
    canvas = response.json()
    print " * We have a canvas: %d" % (canvas['id'])    
    
    return canvas
    

def ask_for_socket(code, port=False):
    " Ask for a socket with a handler running the code."

    if port:
        thread = LocalServer(None, code, port)
        thread.start()
        return ('localhost:%d' % (port, ), thread)
    
    canvas = create_canvas(code)

    # Create canvas and session.
    s = requests.Session()
    s.headers = {'Content-Type': 'application/json'}

    # Create a session for this canvas.
    response = s.post(SERVER_BASE + '/api/v1/canvas_sessions/',
                      json.dumps({'canvas': canvas['id']}))

    if response.status_code != 201:
        raise Exception("API error creating the Canvas.")

    # Canvas Session.
    canvas_session = response.json()
    print " * We have a session!"

    # Wait for socket.
    websocket = None
    print " * Waiting to receive a socket:"
    for i in range(20):

        print ".", 
        sys.stdout.flush()

        # Ask for canvas session and check the socket field.
        response = s.get(canvas_session['self'])
        if response.status_code == 200:            
            data = response.json()
            websocket = data['socket']
            if websocket is not None:
                print ""
                break

        time.sleep(1)

    if websocket is None:
        print "Socket was not received :("
        raise Exception("Socket was not received")

    # # Get websocket location.
    print " * We have a socket in %s" % (websocket, )

    return (websocket, canvas_session['id'])

def destroy_socket(session_id):
    " Destroy the previously created socket."
    
    if isinstance(session_id, threading.Thread):
        session_id.stop()
        
    else:
        # Delete session.
        pass


def run(python_code, local=False):
    """ Run a tornado web server. """

    socket, session_id = ask_for_socket(python_code, local)
        
    
def test(python_code, name, kwargs, local=False):    

    # Ask for a socket.
    socket, session_id = ask_for_socket(python_code, local)

    # Request.
    response = requests.get('http://%s/%s' % (socket, name), params={'kwargs': kwargs})

    if response.status_code == 200:
        print "We have a response: %s" % (str(response.content), )
    else:
        print " :) An error: %s" % (str(response.content), )        

    # Destroy the socket.
    destroy_socket(session_id)
        

def main(argv=None):

    # Build argument parser.
    parser = argparse.ArgumentParser(description='Giving life to your data.')

    # Python code.
    parser.add_argument('-P', '--python', help="File with python code.", dest="python", default=False)

    # Run the server.
    parser.add_argument('--run', help="Run the server.", action="store_true", default=False)

    # Run the server.
    parser.add_argument('--local', help="Run the server locally", action="store_true", default=False)
    parser.add_argument('--port', type=int, help="Local server in this port", default=8888)
    
    # Test a function.
    parser.add_argument('--test', help="Test a function", default=False)

    # kwards for the tested function.
    parser.add_argument('--kwargs', help="Keyword arguments to sent to the function as json. eg: '{\"x\": 1}'", default="{}")

    # Give an html page.
    parser.add_argument('-H', '--html', help="Html for the canvas view.", dest='html', default=False)

    # Canvas parameter.
    parser.add_argument('--canvas', help="Create a new canvas.", action="store_true", default=False)

    # Parse.
    args = parser.parse_args(argv)

    if args.run:

        # Read the python code.
        with open(args.python, 'r') as fd:
            python_code = fd.read()

        # Run the code.
        run(python_code, local=args.local)

    if args.test:        

        # Read the python code.
        with open(args.python, 'r') as fd:
            python_code = fd.read()
    
        # Test the function.
        test(python_code, args.test, args.kwargs, local=args.port if args.local else False)

    
    # Get the html code.
    html_code = None
    if args.html:
        # Read html code.
        with open(args.html, 'r') as fd:
            html_code = fd.read()
    
    # Get the python code.
    python_code = None
    if args.python:
        # Read python code.
        with open(args.python, 'r') as fd:
            python_code = fd.read()

    if args.canvas:        
        create_canvas(python_code)

    # If also local use the same port to execute the functions.
    elif html_code != None: 
        # Run tornado with this webpage.
        t = LocalServer(html_code, python_code, args.port)
        t.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            t.stop()


