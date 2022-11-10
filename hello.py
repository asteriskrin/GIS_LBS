from flask import Flask, render_template, send_from_directory, request
import json
import requests
import urllib.parse
import numpy as np

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

'''
getSegmentData

Return:
[geometry, distance, duration]
'''
def getSegmentData(from_pos, to_pos):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving-traffic/{from_pos[1]},{from_pos[0]};{to_pos[1]},{to_pos[0]}?access_token={MAPBOX_TOKEN}"
    resp = requests.get(url)
    if resp.status_code == 200:
        response_object = json.loads(resp.content)
        try:
            return [response_object['routes'][0]['geometry'],
                response_object['routes'][0]['distance'],
                response_object['routes'][0]['duration']]
        except:
            raise Exception("Could not extract geometry data") 
    else:
        return None

'''
run_nna

Return:
[waypoints, geometry]
'''
def run_nna(vehicle_capacity, nodes, matrix_geometry, matrix_distance, matrix_duration, node_size):
    tour = []
    subtour = [0]
    curr_cap = 0
    visited = [0]
    while len(visited) < node_size:
        cand_id = None
        cand_val = 99999999999
        for id in range(node_size):
            if subtour[-1] != id and id not in visited:
                dist = matrix_distance[subtour[-1]][id]
                dur = matrix_duration[subtour[-1]][id]

                # We only use distance for now
                val = dur

                # Compare
                if val < cand_val and curr_cap + nodes[id][2] <= vehicle_capacity:
                    cand_id = id
                    cand_val = val

        # No more result, make a new tour
        if not cand_id:
            tour.append(subtour)
            subtour = [0]
            curr_cap = 0
        else:
            visited.append(cand_id)
            subtour.append(cand_id)
            curr_cap += nodes[cand_id][2]
    if subtour:
        tour.append(subtour)
    return tour

@app.route('/run', methods=["POST"])
def run():
    errors = []

    depot = [float(request.form['depot-lat']), float(request.form['depot-lng']), int(0), 'Depot']

    vehicle_capacity = int(request.form['vehicle-capacity'])

    dest_lat = request.form.getlist('destination-lat[]')
    dest_lng = request.form.getlist('destination-lng[]')
    dest_cap = request.form.getlist('destination-cap[]')

    nodes = [depot]
    for i in range(len(dest_lat)):
        nodes.append([float(dest_lat[i]), float(dest_lng[i]), int(dest_cap[i]), f'Destination #{i}'])

    node_size = len(nodes)
    matrix_duration = np.zeros((node_size, node_size))
    matrix_distance = np.zeros((node_size, node_size))
    matrix_geometry = [[""]*node_size]*node_size

    for i in range(node_size):
        for j in range(node_size):
            if i == j:
                matrix_distance[i][j] = 0.0
                matrix_duration[i][j] = 0.0
            else:
                segment_data = getSegmentData([nodes[i][0], nodes[i][1]], [nodes[j][0], nodes[j][1]])
                matrix_geometry[i][j] = segment_data[0]
                matrix_distance[i][j] = segment_data[1]
                matrix_duration[i][j] = segment_data[2]

    tour = run_nna(vehicle_capacity, nodes, matrix_geometry, matrix_distance, matrix_duration, node_size)
    result = []
    # Iterate subtour
    for t in tour:
        waypoints = []
        geometry = []
        curr_pos = 0
        for id in t:
            waypoints.append(nodes[id])
            geometry.append(matrix_geometry[curr_pos][id])
            curr_pos = id
        result.append({
            "waypoint": waypoints,
            "geometry": geometry
        })

    return render_template("index.html", result=result)

@app.route('/intro')
def intro():
    return render_template('intro.html')