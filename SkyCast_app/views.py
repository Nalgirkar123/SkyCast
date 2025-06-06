from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime, timedelta
import os

def index(request):
    weather_data = None
    chart_data = {}
    hourly_chart_data = {}
    news_data = []
    sunrise_time = None
    sunset_time = None
    timezone_name = None
    day_length = None
    local_time = None
    golden_hour_start = None
    golden_hour_end = None
    city = None

    # ✅ Read API keys from environment (production-ready)
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')

    if not OPENWEATHER_API_KEY or not NEWS_API_KEY:
        raise Exception("API keys are missing. Make sure they are set in the environment.")

    if request.method == 'POST':
        city = request.POST.get('city')

    if city:
        # 🌦 Current Weather API
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric'
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()

            weather_main = weather_data['weather'][0]['main']
            weather_data['weather_main'] = weather_main

            chart_data = {
                'labels': ['Actual', 'Feels Like', 'Max', 'Min'],
                'values': [
                    weather_data['main']['temp'],
                    weather_data['main']['feels_like'],
                    weather_data['main']['temp_max'],
                    weather_data['main']['temp_min']
                ]
            }

            sunrise_unix = weather_data['sys']['sunrise']
            sunset_unix = weather_data['sys']['sunset']
            timezone_offset = weather_data['timezone']

            sunrise_dt = datetime.utcfromtimestamp(sunrise_unix + timezone_offset)
            sunset_dt = datetime.utcfromtimestamp(sunset_unix + timezone_offset)

            sunrise_time = sunrise_dt.strftime('%H:%M')
            sunset_time = sunset_dt.strftime('%H:%M')

            day_duration = sunset_dt - sunrise_dt
            day_length = str(day_duration)

            local_time_dt = datetime.utcnow() + timedelta(seconds=timezone_offset)
            local_time = local_time_dt.strftime('%m/%d/%Y, %I:%M:%S %p')

            if timezone_offset >= 0:
                timezone_name = f"UTC+{timezone_offset // 3600}"
            else:
                timezone_name = f"UTC{timezone_offset // 3600}"

            golden_hour_start = (sunrise_dt + timedelta(minutes=30)).strftime('%H:%M')
            golden_hour_end = (sunset_dt - timedelta(minutes=30)).strftime('%H:%M')

            # ⏰ Hourly Forecast
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']
            forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric'
            forecast_response = requests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                hourly_labels = []
                hourly_temps = []

                for forecast in forecast_data['list'][:8]:
                    time = forecast['dt_txt'].split(' ')[1][:5]
                    temp = forecast['main']['temp']
                    hourly_labels.append(time)
                    hourly_temps.append(temp)

                hourly_chart_data = {
                    'labels': hourly_labels,
                    'values': hourly_temps
                }

    # 📰 News API
    try:
        if city:
            news_url = f'https://newsapi.org/v2/everything?q={city}&language=en&apiKey={NEWS_API_KEY}'
        else:
            news_url = f'https://newsapi.org/v2/top-headlines?country=in&category=general&language=en&apiKey={NEWS_API_KEY}'

        news_response = requests.get(news_url)
        if news_response.status_code == 200:
            news_data = news_response.json().get('articles', [])[:4]
    except Exception:
        news_data = []

    return render(request, 'index.html', {
        'weather_data': weather_data,
        'chart_data': chart_data,
        'news_data': news_data,
        'sunrise_time': sunrise_time,
        'sunset_time': sunset_time,
        'timezone_name': timezone_name,
        'hourly_chart_data': hourly_chart_data,
        'day_length': day_length,
        'local_time': local_time,
        'golden_hour_start': golden_hour_start,
        'golden_hour_end': golden_hour_end,
        'city': city
    })


def get_weather_by_location(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    api_key = os.getenv('OPENWEATHER_API_KEY')

    if not api_key:
        return JsonResponse({'error': 'API key not configured'}, status=500)

    if lat and lon:
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        response = requests.get(url)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': 'Weather not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
