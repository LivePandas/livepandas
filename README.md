
LivePandas
==========

[![Build Status](https://travis-ci.org/jorgeecardona/livepandas.png)](https://travis-ci.org/jorgeecardona/livepandas)

Command line tool and library to run your own visualization and upload them to livepandas.com



Installation
------------

This is pretty beta at this moment but you can install it from pip using:

```bash
pip install livepandas
```

The package has a few dependencies which are pretty basic and standard.


Usage
-----

This tool will let you use livepandas.com in different ways. You can start by debugging your python and html code, running locally the system and then upload the files to our servers.


What is a Canvas?
-----------------

We call Canvas to the combination of view (html/css/js) and backend code (python) that ultimately defines a single page that build a visualization for your data.

The basic components are a python script that mostly is a single python file and a html file wish possible some static resources as css/js files or images.


Test the python code of a canvas
--------------------------------

Create a python file with the code you want to delegate, the function names must start with `livepandas_` to be delegated to our servers. Eg:

```python
# Published as 'addition'
def livepandas_addition(x, y):
    return x + y

# Not published.
def subtract(x, y):
    return x - y

# Published as 'subtract'
def livepandas_subtract(x, y):
    return substract(x, y)
```

The code can be tested directly fro the command line using:

```bash
livepandas -P code.py --test addition --kwargs '{"x": 1, "y": 2}'
```

Notice the json format for the kwargs, this will give you some freedom to test your code with arbitrary data.

You can also start a server with the code and use it from your machine:

```bash
livepandas -P code.py
```

or

```bash
livepandas -P code.py --port 9999
```

this will start a local server listening by default in the port 8888. For the example above the functions will be accesible at /addition and /subtract for GET requests and /addition/ws and /subtract/ws as websockets.

To test the servers use javascript or python like:

```python
import requests
import json

response = requests.get('http://localhost:8888/addition', 
                        params={'kwargs': json.loads({'x': 1, 'y': 1})})
print response.json()['result']
```

Upload the canvas code
----------------------

You can upload the code using the next command (it will ask for authentication):

```bash
livepandas --new -P code.py
```
or
```bash
livepandas -P code.py --new --username jorgeecardona

```
or
```bash
livepandas -P code.py --new --username jorgeecardona --key 123456789abcdef123456789abcdef
```

A canvas will be added to your account and you will be provided with an id for further usage.

A Canvas is still not accesible you need to create a canvas session which consists of a similar server listening in a public address on internet that execute your code.

Testing the code in our servers
-------------------------------

For this you will need to create an account in the webpage, go to: http://livepandas.com/accounts/register. You will see in your profile a button to create API keys, create one, you will need it to upload the code.

The process of create a canvas is simple just execute:

```bash
livepandas -P code.py --new
```
this will ask for username and API key, or add them as:

```bash
livepandas -P code.py --new --username jorgeecardona --key 123456789abcdef123456789abcdef
```

The process will create a new canvas, it will report the id and the published functions.

You will know how to use this information in a moment to actually get a living server in our infrastructure.

Test the html/js/css code
-------------------------

You can run in a local server your code with the command:


```bash
livepandas -P code.py -H view.html
```

Just as before but you have now the html code for the view and you can use the functions from the file `code.py`. Check on the example directory for some simple cases, you can use cdnjs.com to get the most used js libraries. But don't worry you would be able to use a `static` directory to host any static asset you need.

Notice that the most basic way to use this is with a javascript code like this:

```javascript
$(document).ready(function () {
  $('input').on('change keydown keyup', function () {
    // Get values.
    var x = parseInt($("input[name='x']").val(), 10);
    var y = parseInt($("input[name='y']").val(), 10);      
    $.getJSON('/add', {kwargs: JSON.stringify({x: x, y:y})}, function (d, s, x) {
      $('h2').html("Result: " + d.result);
    });
  });      
});
```

This code wait for changes in two inputs and then send the values to a function that add them and put the result back in a title.

Can you imagine doing some nice fft over huge data like this?

Run html local and python in our servers
----------------------------------------

In this case you can create the canvas first using:

```bash
livepandas --new -P code.py
```

This will give you a canvas id, then you can do something like this:

```javascript

window.canvas_id = 1;
window.session_id = null;

function wait_for_socket() {
 
  // Url of the session resource.
  var url = 'http://livepandas.com/api/v1/canvas_sessions/' + window.session_id + '/';

  $.getJSON(url, function(d,s,x){
    if (d.socket != null) {
      // Nice valid socket, we can use it to add numbers!!!
      $('h2#socket').html('Using socket: ' + d.socket);
      $('input').on('change keydown keyup', function () {
        // Get values.
        var x = parseInt($("input[name='x']").val(), 10);
        var y = parseInt($("input[name='y']").val(), 10);      
        $.getJSON('http://' + d.socket + '/add', {kwargs: JSON.stringify({x: x, y:y})}, function (d, s, x) {
          $('h2#result').html("Result: " + d.result);
        });
      });        
    } else {
      // Wait a second and try again.
      setTimeout(wait_for_socket, 1000);
    }
  });
}

$(document).ready(function () {			   
  // Create the canvas session in here.
  var url = 'http://livepandas.com/api/v1/canvas_sessions/';			   
  $.post(url, {canvas: canvas_id}, function(d, s, x) {
    window.session_id = d.id;
    // Wait for the valid socket.
    wait_for_socket();
  });  
});
```

It basically creates a session, waits for a valid websocket and then use it to add the numbers.

Notice that you can use this from Backbone too, and virtually from any js helper library.

WebSockets? Hell yeah!
----------------------

Every server will have a copy for websockets at `/method/ws`, you can see a similar example as above using websockets:

```javascript

window.canvas_id = 75;

function prepare_socket(websocket, name) {

  $('h2#socket').html('Using WebSocket: ' + websocket);

  // Create a WebSocket
  var ws = new WebSocket("ws://" + websocket + "/" + name + "/ws");

  // On Message.
  ws.onmessage = function (evt) {
    var data = JSON.parse(evt.data);
    if ('result' in data) 
      $('h2#result').html("Result: " + data['result']);  
  }

  // Wait for changes in the text.
  $('input').on('change keydown keyup', function () {
    // Get values.
    var x = parseInt($("input[name='x']").val(), 10);
    var y = parseInt($("input[name='y']").val(), 10);
    ws.send(JSON.stringify({x: x, y:y}))  
  });
}

function wait_for_socket() {
 
  // Url of the session resource.
  var url = 'http://livepandas.com/api/v1/canvas_sessions/' + window.session_id + '/';

  $.getJSON(url, function(d,s,x){
    if (d.socket != null) {
      // Prepare Socket to be used.
      prepare_socket(d.socket, 'add');
    } else {
      // Wait a second and try again.
      setTimeout(wait_for_socket, 1000);
    }
  });
}

$(document).ready(function () {			   
  var url = 'http://livepandas.com/api/v1/canvas_sessions/';			   
  $.post(url, {canvas: canvas_id}, function(d, s, x) {
    window.session_id = d.id;
    wait_for_socket();
  });  
});
```

### Creating the socket from CLI

First we need to upload the python code to our servers or run it locally as:

```bash
livepandas -P code.py --new --username jorgeecardona
```
or

```bash
livepandas -P code.py
```

In the first case you will get an Id for the new canvas, and is going to show up in your home page at www.livepandas.com. In the second case you will get a socket to connect running the code. 

If your using our servers you still need to create a session to use the code, but don't worry this is easy step. With javascript we need first to get a _canvas session_ object using the endpoint `/api/v1/canvas-sessions/` as: ()

```javascript

// Change the canvas id.
window.canvas_id = 1;

$.post('http://www.livepandas.com/api/v1/canvas_sessions/', {
    canvas: window.canvas_id
});
```
It will take approximately 3 seconds to create a websocket, fetch again the session with a get:
```javacript
$.getJSON('http://www.livepandas.com/api/v1/canvas_sessions/3/', function (data, textStatus, jqXHR) {
    alert(data.socket);
});
```

Now we have a socket to connect. This socket will be alive during the session, and the session is alive during the next 5 minutes of the last api interaction, so, try to do some get to the canvas session to keep it alive.

#### Using the socket

Well, this is pretty straightforward javascript code:

```javascript
$.getJSON(socket, {kwargs: JSON.stringify({x: 1, y: 2}), function (data, textStatus, jqXHR) {
    alert(data.result);
});
```

So, notice that you need to force the json format too, since you may be using any library sending all the params either in `application/json` or `application/x-www-form-urlencoded`.

### Streaming the response

More on this later.