from flask import Flask, request, jsonify, render_template
import http.client
import json
import urllib.parse
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel
import os
import re
from flask_cors import CORS

app = Flask(__name__, static_folder='./frontend/build', static_url_path='/')
CORS(app)  # Enable CORS for all routes

# Load Vertex AI credentials
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if not credentials_path:
    credentials_path = r'smart-emission-09aee1175355.json'  # Replace with your actual path

try:
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    vertexai.init(project="smart-emission", location="us-central1", credentials=credentials)
    gemini_model = GenerativeModel("gemini-pro")
except Exception as e:
    print(f"Error initializing Vertex AI: {e}")

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
        
        # Parse the JSON response
        raw_data = json.loads(data)
        
        # Check if stations exist in the response
        if 'stations' in raw_data and len(raw_data['stations']) > 0:
            # Take the first station's data
            station = raw_data['stations'][0]
            
            # Create a dictionary with the specific fields
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

def format_gemini_output(text):
    """Formats the Gemini output into structured HTML."""
    # Split the response into sections based on headings
    sections = re.split(r'##\s*(.*?)\s*\n', text)
    formatted_html = ""

    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):  # Check to ensure we don't access beyond array bounds
            heading = sections[i]
            content = sections[i + 1].strip()

            # Format lists
            content = re.sub(r'\*\s(.*?)\n', r'<li>\1</li>', content)
            if '<li>' in content:
                content = f'<ul>{content}</ul>'

            # Format paragraphs
            content = re.sub(r'([^*<\n]+)\n', r'<p>\1</p>', content)

            formatted_html += f"<h2>{heading}</h2>{content}"

    return formatted_html

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

@app.route('/api/gemini-insights', methods=['POST'])
def gemini_insights():
    data = request.json
    city = data.get('city', '').strip()
    
    if not city:
        return jsonify({"error": "City name is required"}), 400
    
    try:
        # Generate decarbonization insights using Gemini
        prompt = f"Give me decarbonization insights for {city}"
        gemini_response = gemini_model.generate_content(prompt)
        formatted_insights = format_gemini_output(gemini_response.text)
        
        return jsonify({"gemini_insights": formatted_insights})
    except Exception as e:
        return jsonify({"error": f"Error generating insights: {str(e)}"}), 500

@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

if __name__ == '__main__':
    app.run(debug=True)
