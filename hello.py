from flask import Flask, render_template, send_from_directory, request
import json
import requests
import urllib.parse

MAPBOX_TOKEN = "pk.eyJ1IjoiYXN0ZXJpc2tyaW4iLCJhIjoiY2xhNm9mMnJwMXBteTN2cGg0dGlzOXlqdSJ9.ePzEH5xX7_B3aty_s9V7OQ"

app = Flask(__name__)

@app.route('/')
def hello():
    return render_template('index.html')

# def getLatLngFromAddress(addr):
#     url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{urllib.parse.quote(addr)}.json?country=ID&access_token={MAPBOX_TOKEN}"
#     resp = requests.get(url)
#     if resp.status_code == 200:
#         try:
#             coords = json.loads(resp.content)['features'][0]['geometry']['coordinates']
#             print (json.loads(resp.content))
#             return [coords[1], coords[0]]
#         except:
#             raise Exception("Could not extract latitude and longtitude data from address " + addr)
#     else:
#         return []

def getGeometry(from_pos, to_pos):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{from_pos[1]},{from_pos[0]};{to_pos[1]},{to_pos[0]}?access_token={MAPBOX_TOKEN}"
    resp = requests.get(url)
    if resp.status_code == 200:
        response_object = json.loads(resp.content)
        try:
            return response_object['routes'][0]['geometry']
        except:
            raise Exception("Could not extract geometry data") 
    else:
        return None

@app.route('/run', methods=["POST"])
def run():
    errors = []

    depot = [request.form['depot-lat'], request.form['depot-lng']]

    dest_lat = request.form.getlist('destination-lat[]')
    dest_lng = request.form.getlist('destination-lng[]')
    destinations = []
    for i in range(len(dest_lat)):
        destinations.append([dest_lat[i], dest_lng[i]])

    waypoints = [depot]
    geometry = []
    curr_position = depot
    for d in destinations:
        waypoints.append(d)
        g = getGeometry(curr_position, d)
        geometry.append(g)
        curr_position = d

    response_reply = {
        "waypoints": waypoints,
        "geometry": geometry
    }

    return render_template("index.html", result=response_reply)

@app.route('/intro')
def intro():
    return render_template('intro.html')