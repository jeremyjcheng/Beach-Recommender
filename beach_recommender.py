import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import googlemaps
import requests
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
import numpy as np
import warnings

# Suppress warnings from ARIMA
warnings.filterwarnings('ignore')

# Load API Keys from environment variables
weather_api_key = os.getenv("WEATHER_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# Initialize Flask and Google Maps
app = Flask(__name__)
gmaps = googlemaps.Client(key=google_api_key)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

def geocode_place(place_name):
    """Convert a place name into latitude and longitude using the Google Geocoding API."""
    geocode_result = gmaps.geocode(place_name)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        return None, None

def find_nearby_beaches(lat, lng, radius=10000):
    """Find nearby beaches within a given radius (in meters) from a specific location (latitude, longitude)."""
    places_result = gmaps.places_nearby(
        location=(lat, lng),
        radius=radius,
        keyword='beach'
    )
    
    beaches = []
    unique_beach_names = set()
    
    if places_result.get('results'):
        for place in places_result['results']:
            name = place.get('name')
            if name not in unique_beach_names:  # Check for duplicate beach names
                location = place.get('geometry', {}).get('location', {})
                beach_lat = location.get('lat')
                beach_lng = location.get('lng')
                beaches.append({
                    'name': name,
                    'latitude': beach_lat,
                    'longitude': beach_lng
                })
                unique_beach_names.add(name)

    return beaches[:5]

def get_historical_weather_data(lat, lng, days=10):
    """Fetch historical marine weather data for the last `days` days from the Storm Glass API."""
    today = datetime.utcnow()
    start = today - timedelta(days=days)
    
    parameters = ['waveHeight', 'wavePeriod', 'windSpeed', 'swellHeight']
    
    response = requests.get(
        'https://api.stormglass.io/v2/weather/point',
        params={
            'lat': lat,
            'lng': lng,
            'params': ','.join(parameters),
            'start': int(start.timestamp()), 
            'end': int(today.timestamp())
        },
        headers={'Authorization': weather_api_key}
    )
    
    if response.status_code == 200:
        json_data = response.json()
        data = []
        for hour in json_data['hours']:
            # Safely retrieve data from the 'noaa' source, or use None if missing
            data.append({
                'time': hour['time'],
                'waveHeight': hour['waveHeight'].get('noaa', None),
                'wavePeriod': hour['wavePeriod'].get('noaa', None),
                'windSpeed': hour['windSpeed'].get('noaa', None),
                'swellHeight': hour['swellHeight'].get('noaa', None),
            })
        return data
    else:
        return None

def apply_arima_forecasting(data, parameter):
    """Apply ARIMA model to forecast future values for the selected parameter."""
    values = np.array([entry[parameter] for entry in data if entry[parameter] is not None])
    
    if len(values) == 0:
        return None
    
    model = ARIMA(values, order=(5, 1, 0))
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=5)
    return forecast

def get_weather_for_multiple_beaches(beaches, days=10):
    """Fetch historical weather data and apply ARIMA model for multiple beaches."""
    beach_forecast_data = {}
    
    for beach in beaches:
        lat = beach['latitude']
        lng = beach['longitude']
        name = beach['name']
        
        historical_data = get_historical_weather_data(lat, lng, days)
        
        if historical_data:
            wave_forecast = apply_arima_forecasting(historical_data, 'waveHeight')
            period_forecast = apply_arima_forecasting(historical_data, 'wavePeriod')
            wind_forecast = apply_arima_forecasting(historical_data, 'windSpeed')
            swell_forecast = apply_arima_forecasting(historical_data, 'swellHeight')
            
            beach_forecast_data[name] = {
                'waveHeight': wave_forecast,
                'wavePeriod': period_forecast,
                'windSpeed': wind_forecast,
                'swellHeight': swell_forecast
            }
            
    return beach_forecast_data

def get_current_weather_data(lat, lng):
    """Fetch current marine weather data"""
    today = datetime.utcnow()  # Get the current UTC time
    
    parameters = ['waveHeight', 'wavePeriod', 'windSpeed', 'swellHeight']
    
    response = requests.get(
        'https://api.stormglass.io/v2/weather/point',
        params={
            'lat': lat,
            'lng': lng,
            'params': ','.join(parameters),
            'source': 'noaa',
            'start': int(today.timestamp()),  # Fetch current data
            'end': int(today.timestamp())     # Use the same timestamp for "current" data
        },
        headers={'Authorization': weather_api_key}
    )
    
    if response.status_code == 200:
        json_data = response.json()
        # Fetch the current hour's data
        current_data = json_data['hours'][0] if 'hours' in json_data else None
        
        if current_data:
            return {
                'waveHeight': current_data.get('waveHeight', {}).get('noaa', None),
                'wavePeriod': current_data.get('wavePeriod', {}).get('noaa', None),
                'windSpeed': current_data.get('windSpeed', {}).get('noaa', None),
                'swellHeight': current_data.get('swellHeight', {}).get('noaa', None),
            }
        return None
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

def meters_to_feet(meters):
    return round(meters * 3.28084, 2)

def mps_to_mph(mps):
    return round(mps * 2.23694, 2)

def rank_beaches(beach_forecast_data, user_surfing_level):
    rankings = []
    
    if user_surfing_level == "beginner":
        weights = {'waveHeight': 0.4, 'wavePeriod': 0.2, 'windSpeed': 0.2, 'swellHeight': 0.2}
    elif user_surfing_level == "intermediate":
        weights = {'waveHeight': 0.3, 'wavePeriod': 0.3, 'windSpeed': 0.2, 'swellHeight': 0.2}
    else:
        weights = {'waveHeight': 0.2, 'wavePeriod': 0.4, 'windSpeed': 0.2, 'swellHeight': 0.2}

    for beach, forecasts in beach_forecast_data.items():
        score = (np.mean(forecasts['waveHeight']) * weights['waveHeight'] +
                 np.mean(forecasts['wavePeriod']) * weights['wavePeriod'] +
                 np.mean(forecasts['windSpeed']) * weights['windSpeed'] +
                 np.mean(forecasts['swellHeight']) * weights['swellHeight'])
        
        rankings.append((beach, score))
    
    rankings.sort(key=lambda x: x[1], reverse=True)
    return rankings


# Routes
@app.route('/')
def index():
    surfing_level = session.get('surfing_level', '')
    return f'''
        <h1>Beach Recommender</h1>
        <form action="/recommend" method="POST">
            <label for="location">Enter your current location:</label>
            <input type="text" id="location" name="location" required><br>
            <label for="surfing_level">Enter your surfing ability (beginner, intermediate, advanced):</label>
            <input type="text" id="surfing_level" name="surfing_level" value="{surfing_level}" required><br>
            <button type="submit">Get Recommendations</button>
        </form>
    '''

@app.route('/recommend', methods=['POST'])
def recommend():
    # Get the form data
    location = request.form['location']
    surfing_level = request.form['surfing_level']
    
    # Store the surfing ability in the session
    session['surfing_level'] = surfing_level
    
    # Geocode the location
    lat, lng = geocode_place(location)
    
    if lat is None or lng is None:
        return "Error: Could not find the location."

    # Find nearby beaches
    nearby_beaches = find_nearby_beaches(lat, lng)
    
    if not nearby_beaches:
        return '''
            <h1>No Nearby Beaches Found</h1>
            <p>Unfortunately, we couldn't find any beaches near your location.</p>
            <form action="/" method="get">
                <button type="submit">Try Again</button>
            </form>
        '''

    # Get weather data and rank beaches
    beach_forecasts = get_weather_for_multiple_beaches(nearby_beaches)
    ranked_beaches = rank_beaches(beach_forecasts, surfing_level)

    # Display the ranked beaches with surf conditions
    result = '<h1>Beach Recommendations with Current Conditions</h1><ol>'
    for rank, (beach, score) in enumerate(ranked_beaches, start=1):
        forecast = beach_forecasts[beach]
        
        # Convert and display in both units
        wave_height_m = round(forecast['waveHeight'][0], 2) if forecast['waveHeight'] is not None else "N/A"
        wave_height_ft = round(meters_to_feet(wave_height_m), 2) if wave_height_m != "N/A" else "N/A"
        wind_speed_mps = round(forecast['windSpeed'][0], 2) if forecast['windSpeed'] is not None else "N/A"
        wind_speed_mph = round(mps_to_mph(wind_speed_mps), 2) if wind_speed_mps != "N/A" else "N/A"
        wave_period = round(forecast['wavePeriod'][0], 2) if forecast['wavePeriod'] is not None else "N/A"
        swell_height = round(forecast['swellHeight'][0], 2) if forecast['swellHeight'] is not None else "N/A"
        
        result += f'<li><strong>{beach}</strong><br>'
        result += f"Wave Height: {wave_height_m} meters / {wave_height_ft} feet<br>"
        result += f"Wave Period: {wave_period} seconds<br>"
        result += f"Wind Speed: {wind_speed_mps} m/s / {wind_speed_mph} mph<br>"
        result += f"Swell Height: {swell_height} meters<br>"
        result += f"Score: {round(score, 2)}</li><br>"
    result += '</ol>'
    
    # Add option to try a different location
    result += '''
        <br><form action="/" method="get">
            <button type="submit">Try a Different Location</button>
        </form>
    '''
    
    return result

# Main driver function
if __name__ == '__main__':
    app.run(debug=True)