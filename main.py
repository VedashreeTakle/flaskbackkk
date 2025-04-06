from flask import Flask, request, jsonify, render_template
import http.client
import json
import urllib.parse
import os
import re
from flask_cors import CORS

app = Flask(__name__, static_folder='./frontend/build', static_url_path='/')
CORS(app)  # Enable CORS for all routes


def get_air_quality_by_city(city):
    """
    Retrieve specific air quality details for a given city
    """
    try:
        conn = http.client.HTTPSConnection("api.ambeedata.com")

        headers = {
            'x-api-key': "94d71de3b1fed41336c4b0a2784c7c4bd869ff1c130c0325809c73bf54cee9bd",
            'Content-type': "application/json"
        }

        # URL encode the city name
        encoded_city = urllib.parse.quote(city)
        
        # Construct the API endpoint
        endpoint = f"/latest/by-city?city={encoded_city}"
        
        conn.request("GET", endpoint, headers=headers)

        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        raw_data = json.loads(data)
        
        # Check if stations exist in the response
        if 'stations' in raw_data and len(raw_data['stations']) > 0:
            # Take the first station's data
            station = raw_data['stations'][0]
            
            specific_data = {
                "AQI": station.get('AQI', 'N/A'),
                "CO": station.get('CO', 'N/A'),
                "NO2": station.get('NO2', 'N/A'),
                "OZONE": station.get('OZONE', 'N/A'),
                "PM10": station.get('PM10', 'N/A'),
                "PM25": station.get('PM25', 'N/A'),
                "SO2": station.get('SO2', 'N/A'),
                "aqiInfo": station.get('aqiInfo', {
                    "category": "N/A",
                    "concentration": "N/A",
                    "pollutant": "N/A"
                }),
                "city": station.get('city', city),
                "updatedAt": station.get('updatedAt', 'N/A')
            }
            
            return specific_data
        else:
            return {"error": f"No air quality data found for {city}"}
    
    except Exception as e:
        return {"error": str(e)}


@app.route('/api/air-quality', methods=['POST'])
def air_quality():
    data = request.json
    city = data.get('city', '').strip()
    
    if not city:
        return jsonify({"error": "City name is required"}), 400
    
    air_quality_data = get_air_quality_by_city(city)
    
    if 'error' in air_quality_data:
        return jsonify({"error": air_quality_data['error']}), 404
    
    return jsonify({"air_quality_data": air_quality_data})


# Serve React app
@app.route('/')
def serve():
    return {"welcome":"hello"}

if __name__ == '__main__':
    app.run(debug=True)
