from flask import Flask, render_template, send_from_directory, request
import json
import requests
import urllib.parse
import numpy as np
from classes.ThreadWithResult import ThreadWithResult

MAPBOX_TOKEN = "PASTE_HERE"

app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('index.html')

'''
getSegmentData

Return:
[geometry, distance, duration]
'''
def getSegmentData(from_pos, to_pos):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{from_pos[1]}%2C{from_pos[0]}%3B{to_pos[1]}%2C{to_pos[0]}?alternatives=true&geometries=polyline&language=en&overview=simplified&steps=true&access_token={MAPBOX_TOKEN}"
    resp = requests.get(url)
    requests.encoding = 'ISO-8859-1'
    if resp.status_code == 200:
        response_object = resp.json()
        try:
            return [response_object['routes'][0]['geometry'],
                response_object['routes'][0]['distance'],
                response_object['routes'][0]['duration']]
        except:
            raise Exception("Could not extract geometry data") 
    else:
        raise Exception("API not available")

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
    matrix_geometry = []
    # Making matrix
    for i in range(node_size):
        temp = []
        for j in range(node_size):
            temp.append(None)
        matrix_geometry.append(temp)

    threads_data = []
    for i in range(node_size):
        for j in range(node_size):
            if i == j:
                matrix_distance[i][j] = 0.0
                matrix_duration[i][j] = 0.0
            else:
                t = ThreadWithResult(target=getSegmentData, args=([nodes[i][0], nodes[i][1]], [nodes[j][0], nodes[j][1]],))
                t.start()
                t.join()
                threads_data.append([i, j, t])

    for td in threads_data:
        tdr = td[2].result
        matrix_geometry[td[0]][td[1]] = tdr[0]
        matrix_distance[td[0]][td[1]] = tdr[1]
        matrix_duration[td[0]][td[1]] = tdr[2]


    tour = run_nna(vehicle_capacity, nodes, matrix_geometry, matrix_distance, matrix_duration, node_size)
    result = []
    # Iterate subtour
    for t in tour:
        waypoints = []
        geometry = []
        curr_pos = 0
        for i in range(len(t)):
            id = t[i]
            waypoints.append(nodes[id])
            if id != 0:
                g = matrix_geometry[curr_pos][id]
                # escape string
                g = g.replace('\\', '\\\\')
                geometry.append(g)
                curr_pos = id
        geometry.append(matrix_geometry[t[-1]][0].replace('\\', '\\\\'))
        result.append({
            "waypoint": waypoints,
            "geometry": geometry
        })

    return render_template("index.html", result=result)

@app.route('/intro')
def intro():
    return render_template('intro.html')