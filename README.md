# Beach Recommender Application
This project is a Beach Recommender Application that allows users to get recommendations for nearby beaches based on their current location and surfing skill level. The application fetches real-time and historical weather data, including wave heights, wind speeds, and other surf-related conditions. It uses ARIMA forecasting models to provide weather and wave predictions for multiple beaches and ranks them according to the user’s surfing ability level.

Table of Contents
Features
Technologies
Requirements
Setup and Installation
Usage
Environment Variables
Project Structure
API Integration
ARIMA Model
Routes
License
Features
Location-based Beach Recommendations: Using the Google Maps API, the application geocodes the user’s location and finds nearby beaches within a 10,000-meter radius.
Weather Data Forecasting: It fetches marine weather data, including wave height, wave period, swell height, and wind speed from the Storm Glass API.
ARIMA Forecasting: The app applies the ARIMA (AutoRegressive Integrated Moving Average) model to forecast surf conditions for the next 5 days.
User-specified Surfing Skill Level: The app ranks beaches based on the user's surfing skill level (beginner, intermediate, or advanced).
Real-time Weather Data: The app provides current weather conditions alongside forecasts.
Responsive Design: Basic form-based user interface with HTML to interact with the backend.
Technologies
Python (Flask, requests, numpy, statsmodels)
Flask - Python micro web framework for building the web app.
Google Maps API - Used for geocoding the user's inputted location and finding nearby beaches.
Storm Glass API - Used to retrieve marine weather data.
ARIMA Model - Used for forecasting wave height, wave period, wind speed, and swell height.
Requirements
Python 3.7 or later
API keys for:
Google Maps API for geocoding and place searching
Storm Glass API for marine weather data
Basic knowledge of Flask web development and API integration.
Setup and Installation
Clone the repository:

bash
Copy code
git clone https://github.com/jeremyjcheng/beach_recommender.git
cd beach_recommender
Create and activate a virtual environment:

bash
Copy code
python3 -m venv venv
source venv/bin/activate   # For macOS/Linux
venv\Scripts\activate      # For Windows
Install the required dependencies:

bash
Copy code
pip install -r requirements.txt
Set up your environment variables for API keys and secret keys. Create a .env file in the root of the project with the following contents:

bash
Copy code
WEATHER_API_KEY=your-stormglass-api-key
GOOGLE_API_KEY=your-google-maps-api-key
FLASK_SECRET_KEY=your-flask-secret-key
Run the Flask application:

bash
Copy code
flask run
Open your browser and go to http://127.0.0.1:5000/ to access the application.

Usage
Enter your current location in the form (e.g., a city, landmark, or address).
Specify your surfing ability level: beginner, intermediate, or advanced.
Click Get Recommendations to view a ranked list of beaches nearby, complete with surf forecasts.
Forecasts include:
Wave height in both meters and feet
Wave period in seconds
Wind speed in both meters per second (m/s) and miles per hour (mph)
Swell height in meters
Environment Variables
You will need to set the following environment variables to run the application:

Variable	Description
WEATHER_API_KEY	Your Storm Glass API key to access weather data.
GOOGLE_API_KEY	Your Google Maps API key to geocode and find places.
FLASK_SECRET_KEY	A secret key for Flask session management.
Project Structure
php
Copy code
beach_recommender/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Dependencies required to run the app
├── README.md                   # Project documentation
├── templates/                  # HTML templates for rendering views
│   └── index.html              # HTML page for user input
├── static/                     # Static files (CSS, JS, images)
API Integration
1. Google Maps API:
Geocoding: Converts a user-entered location (place name or address) into latitude and longitude.
Places Nearby Search: Finds nearby beaches within a certain radius using the latitude and longitude coordinates.
2. Storm Glass API:
Marine Weather Data: Fetches wave height, wave period, wind speed, and swell height for a specified location.
Example API Request:
python
Copy code
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
ARIMA Model
The ARIMA model is used to forecast weather parameters such as wave height and wind speed for the next 5 days based on historical weather data.

The model order is (5, 1, 0):
5 for autoregressive terms
1 for difference terms
0 for moving average terms
Example:
python
Copy code
model = ARIMA(values, order=(5, 1, 0))
model_fit = model.fit()
forecast = model_fit.forecast(steps=5)
Routes
/
Method: GET
Description: Displays the homepage where users can input their location and surfing ability level.
/recommend
Method: POST
Description: Processes the user's location and surfing level, fetches nearby beach data, and ranks them based on forecasted weather conditions.
License
This project is licensed under the MIT License. See the LICENSE file for details.

