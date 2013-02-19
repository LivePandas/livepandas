import argparse
import requests
import json
import time
import sys
import threading
import tornado.ioloop
import tornado.web

SERVER_BASE = 'http://livepandas.com'

class LocalServer(threading.Thread):

    def __init__(self, code, port):
        threading.Thread.__init__(self)

        ns = {}
        exec compile(code, '<string>', 'exec') in ns

        # Check for the registered.
        functions = [(k, v) for k, v in ns.items() if k.startswith('livepandas_') and callable(v)]

        class FunctionHandler(tornado.web.RequestHandler):
            def get(self):
                
                try:
                    kwargs = json.loads(self.get_argument('kwargs', '{}'))
                    data = {'result': self.func(**kwargs)}
                except Exception, e:
                    data = {'exception': str(e)}
                    self.set_status(400)
                    
                self.write(json.dumps(data))

        # Define one handler per function.
        handlers = []
        for name, func in functions:
            handler = FunctionHandler
            handler.func = staticmethod(func)
            handlers.append((r"/" + name.replace('livepandas_', '') , handler))

        # Save port.
        application = tornado.web.Application(handlers)
        application.listen(port)

        # IO Loop instance.
        self.ioloop = tornado.ioloop.IOLoop.instance()

    def run(self):
        self.ioloop.start()

    def stop(self):
        self.ioloop.stop()

def ask_for_socket(code, port=False):
    " Ask for a socket with a handler running the code."

    if port:
        thread = LocalServer(code, port)
        thread.start()
        return ('localhost:%d' % (port, ), thread)

    # Create canvas and session.
    s = requests.Session()
    s.headers = {'Content-Type': 'application/json'}

    # Create an anonymous canvas (will be deleted after 5 minutes of the last usage)
    response = s.post(SERVER_BASE + '/api/v1/canvases/', 
                      json.dumps({'python': code, 'author': None}))
    
    if response.status_code != 201:
        raise Exception("API error creating the Canvas.")

    # Canvas created.
    canvas = response.json()
    print " * We have a canvas!"

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
    parser.add_argument('-P', '--python', help="File with python code.", dest="python")

    # Run the server.
    parser.add_argument('--run', help="Run the server.", action="store_true", default=False)

    # Run the server.
    parser.add_argument('--local', help="Run the server locally", action="store_true", default=False)
    parser.add_argument('--port', type=int, help="Local server in this port", default=8888)
    
    # Test a function.
    parser.add_argument('--test', help="Test a function", default=False)

    # kwards for the tested function.
    parser.add_argument('--kwargs', help="Keyword arguments to sent to the function as json. eg: '{\"x\": 1}'", default="{}")

    # Parse.
    args = parser.parse_args(argv)

    if args.run:

        # Read the python code.
        with open(args.python, 'r') as fd:
            python_code = fd.read()

        run(python_code, local=args.local)

    if args.test:        

        # Read the python code.
        with open(args.python, 'r') as fd:
            python_code = fd.read()
    
        # Test the function.
        test(python_code, args.test, args.kwargs, local=args.port if args.local else False)
