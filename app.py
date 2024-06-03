from flask import Flask, request, render_template
import requests
from geopy.geocoders import Nominatim

app = Flask(__name__)


@app.route('/')
def form():
    return render_template('form.html')


@app.route('/recommend', methods=['POST'])
def recommend():
    latitude = request.form['latitude']
    longitude = request.form['longitude']
    light = request.form['light']

    region = get_region_from_coordinates(latitude, longitude)
    climate = get_climate_from_coordinates(latitude, longitude)

    recommendations = get_plant_recommendations(region, climate, light)

    return render_template('recommendation.html', recommendations=recommendations)


def get_region_from_coordinates(lat, lon):
    geolocator = Nominatim(user_agent="plant_recommendations")
    location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
    address = location.raw['address']
    country = address.get('country', '')
    return country


def get_climate_from_coordinates(lat, lon):
    weather_api_key = '0a746bf3706049219aa175817240106'
    url = f'http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={lat},{lon}'
    response = requests.get(url)
    data = response.json()
    humidity = data['current']['humidity']
    precipitation = data['current']['precip_mm']
    temp_c = data['current']['temp_c']
    return {
        'humidity': humidity,
        'precipitation': precipitation,
        'temperature': temp_c
    }


def get_plant_recommendations(region, climate, light):
    trefle_api_key = 'vqk_NprdSLUr29wBZvdgmGLNvCNh4BN472QEJm5OMUk'
    humidity = min(max(climate['humidity'] // 10, 0), 10)
    precipitation = climate['precipitation']
    temperature = climate['temperature']

    url = (f'https://trefle.io/api/v1/plants?token={trefle_api_key}'
           f'&filter[distribution]={region}'
           f'&filter_not[edible_part]=null'
           f'&range[maximum_height_cm]=5,100'
           f'&range[atmospheric_humidity]={humidity}'
           f'&range[minimum_precipitation]={precipitation - 100},{precipitation}'
           f'&range[maximum_precipitation]={precipitation},{precipitation + 100}'
           f'&range[minimum_temperature]={temperature - 10},{temperature}'
           f'&range[maximum_temperature]={temperature},{temperature + 10}'
           f'&filter_not[light]={light}')

    response = requests.get(url)
    data = response.json()

    recommendations = []

    if 'data' in data:
        plants = data['data']
        for plant in plants:
            scientific_name = plant.get('scientific_name')
            common_name = plant.get('common_name')
            family = plant.get('family')
            genus = plant.get('genus')
            photo_url = plant.get('image_url') if 'image_url' in plant else None
            duration = plant.get('duration')
            recommendations.append({
                'scientific_name': scientific_name,
                'common_name': common_name,
                'family': family,
                'genus': genus,
                'photo_url': photo_url,
                'duration': duration
            })

    print("Recomendaciones filtradas:", recommendations)
    return recommendations


if __name__ == '__main__':
    app.run(debug=True)
