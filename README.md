
LivePandas
==========

[![Build Status](https://travis-ci.org/jorgeecardona/livepandas.png)](https://travis-ci.org/jorgeecardona/livepandas)

Command line tool and library to run your own visualization and upload them to livepandas.com

Usage
-----

This tool will let you use livepandas.com in different ways. You can start by debugging your python and html code, running locally the system and then upload the files to our servers.

### Test the Python code

In your python file you need to give a name to the function you want to register starting with `livepandas_`:

```python
def livepandas_addition(x, y):
    return x + y
```

You can test this code locally using the cli with:

```bash
livepandas -P code.py --test addition --kwargs '{"x": 1, "y": 2}' --local
```

or if you want to test it in our servers with:

```bash
livepandas -P code.py --test addition --kwargs '{"x": 1, "y": 2}'
```

Notice the json format for the kwargs, this will give you some freedom to test your code with arbitrary data.

### Test the html/js/css code

To test the html code we can take two approaches, running all the code locally and then run the python code in our servers.

### Running all the code locally

Given two files `view.html` and `code.py` the easiest way to run all the system is using the command:

```bash
livepandas -P code.py -H view.html
```

You can check on the example directory for some simple cases, you can use cdnjs.com to get the most used js libraries. But don't worry you would be able to use a `static` directory to host any static asset you need.

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

### Running just the html locally.

In this case you can create the canvas first using:
```bash
livepandas --canvas -P code.py
```
This will give you a canvas id (without any authentication the canvas will be temporary). then you can use something like this:

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

### Creating the socket from CLI

First we need to upload the python code to our servers or run it locally as:

```bash
livepandas -P code.py --new --username jorgeecardona
```
or

```bash
livepandas -P code.py --new --username jorgeecardona --local
```

In the first case you will get an Id for the new canvas, and is going to show up in your home page at www.livepandas.com, the command will ask for password. In the second case
you will get a socket to connect running the code. 


If your using our servers you still need to create a session to use the codd, but don't worry this is easy step. With javascript we need first to get a `CanvasSession` object using the endpoint `/api/v1/canvas_sessions/` as (change the canvas id approperly):

```javascript
$.post('http://www.livepandas.com/api/v1/canvas_sessions/', {
    canvas: 1
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