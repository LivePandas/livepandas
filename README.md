
LivePandas
==========

[![Build Status](https://travis-ci.org/jorgeecardona/livepandas.png)](https://travis-ci.org/jorgeecardona/livepandas)

Command line tool and library to run your own visualization and upload them to livepandas.com

Usage
-----

First you need to create an html page with the content of your visualization and a python file with the code associated.

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

#### Creating the socket

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