from __future__ import absolute_import

import argparse
import requests
import json
import time
import sys

from .server import LocalServer

SERVER_BASE = 'http://livepandas.com'
SERVER_BASE = 'http://localhost:8000'

def create_canvas(username, key, python=None, html=None):
    """ Create a canvas with the python and html code."""
        
    # Data to sent.
    data = {}

    if python is not None:
        data['python'] = python

    if html is not None:
        data['html'] = html        

    # Create an anonymous canvas (will be deleted after 5 minutes of the last usage)
    response = requests.post(
        SERVER_BASE + '/api/v1/canvases/', json.dumps(data),
        headers={'Content-Type': 'application/json',
                 'Authorization': 'APIKey %s:%s' % (username, key)})

    # Check for correct creation.
    if response.status_code != 201:
        raise Exception("API error creating the Canvas (%d)." % (response.status_code, ))
        
    # Canvas created.
    canvas = response.json()
    print " * We have a canvas: %d" % (canvas['id'])    
    print "   Functions: %s" % (", ".join(canvas['functions']), )
    
    return canvas
    

def ask_for_socket(code, port=False):
    " Ask for a socket with a handler running the code."

    if port:
        thread = LocalServer(None, code, port)
        thread.start()
        return ('localhost:%d' % (port, ), thread)

    # Create a new canvas for this.
    canvas = create_canvas(code)

    # Create a session for this canvas.
    response = requests.post(
        SERVER_BASE + '/api/v1/canvas-sessions/',
        json.dumps({'canvas': canvas['id']}), 
        headers={'Content-Type': 'application/json'})

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

def get_auth(args):
    """ Get the authentication parameters. """

    if args.username is None:
        username = raw_input("Username: ")
        key = raw_input("API key: ")          
        return username, key

    if args.username is None:
        key = raw_input("API key: ")          
        return args.username, key

    return args.username, args.key        

def test_function(python_code, function_name, kwargs):
    """ Test a function locally. """

    print(" * Testing function %s ..." % (function_name, ))

    ns = {}

    exec compile(python_code, '<string>', 'exec') in ns

    # Look for the function.
    if 'livepandas_%s' % (function_name, ) not in ns:
        raise Exception("Function %s not defined." % (function_name, ))

    # Convert kwargs from json.
    kwargs = json.loads(kwargs)

    result = ns['livepandas_%s' % (function_name, )](**kwargs)

    print("   Result: %s." % (result))


def main(argv=None):

    # Build argument parser.
    parser = argparse.ArgumentParser(description='Giving life to your data.')

    # Authentications.
    parser.add_argument('-U', '--username', help="Username for authenticated requests.")
    parser.add_argument('-K', '--key', help="API Key for authenticated requests.")

    # Python code.
    parser.add_argument('-P', '--python', help="File with python code.", 
                        dest="python", default=False)

    # Give an html page.
    parser.add_argument('-H', '--html', help="Html for the canvas view.", 
                        dest='html', default=False)

    # Give the localtion of the static directory.
    parser.add_argument('-S', '--static', help="Static directory used in the html.", 
                        dest='html', default=False)

    # Extra for the local server.
    parser.add_argument('--port', type=int, help="Local server in this port", default=8888)
    
    # Test a function.
    parser.add_argument('--test', help="Test a function", default=False)

    # kwards for the tested function.
    parser.add_argument(
        '--kwargs', 
        help="Keyword arguments to sent to the function as json. eg: '{\"x\": 1}'", 
        default="{}")

    # Create a new canvas parameter.
    parser.add_argument('--new', help="Create a new canvas.", action="store_true", 
                        default=False)

    # Parse.
    args = parser.parse_args(argv)

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

    if args.test:    
        # Test the function.
        test_function(python_code, args.test, args.kwargs)

    elif args.new:        

        # This requests needs authentication.
        username, key = get_auth(args)
        create_canvas(username, key, python=python_code, html=html_code)

    else:
        # Finally assume we want to run the code, assumming locally.

        # Run tornado with this webpage.
        t = LocalServer(html=html_code, python=python_code, port=args.port)
        t.start()

        try:
            while True:
                pass
        except KeyboardInterrupt:
            t.stop()


