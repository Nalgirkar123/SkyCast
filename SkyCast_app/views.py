from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime, timedelta

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

    if request.method == 'POST':
        city = request.POST.get('city')

    if city:
        api_key = '090ccd6c9968e0e7f9bca262bc93b2ee'

        # Current Weather API
        url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric'
        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()

            # Weather background
            weather_main = weather_data['weather'][0]['main']
            weather_data['weather_main'] = weather_main

            # Temperature Chart (Actual, Feels Like, Max, Min)
            chart_data = {
                'labels': ['Actual', 'Feels Like', 'Max', 'Min'],
                'values': [
                    weather_data['main']['temp'],
                    weather_data['main']['feels_like'],
                    weather_data['main']['temp_max'],
                    weather_data['main']['temp_min']
                ]
            }
            
            # 🌅 Sunrise and Sunset
            sunrise_unix = weather_data['sys']['sunrise']
            sunset_unix = weather_data['sys']['sunset']
            timezone_offset = weather_data['timezone']

            sunrise_dt = datetime.utcfromtimestamp(sunrise_unix + timezone_offset)
            sunset_dt = datetime.utcfromtimestamp(sunset_unix + timezone_offset)

            sunrise_time = sunrise_dt.strftime('%H:%M')
            sunset_time = sunset_dt.strftime('%H:%M')

            
            # Day Length
            day_duration = sunset_dt - sunrise_dt
            day_length = str(day_duration)
            
            # Local Time
            local_time_dt = datetime.utcnow() + timedelta(seconds=timezone_offset)
            local_time = local_time_dt.strftime('%m/%d/%Y, %I:%M:%S %p')
            
            timezone_seconds = timezone_offset
            if timezone_seconds >= 0:
                timezone_name = f"UTC+{timezone_seconds//3600}"
            else:
                timezone_name = f"UTC{timezone_seconds//3600}"

            
            # Golden hour (approx 1 hour after sunrise, 1 hour before sunset)
            golden_hour_start = (sunrise_dt + timedelta(minutes=30)).strftime('%H:%M')
            golden_hour_end = (sunset_dt - timedelta(minutes=30)).strftime('%H:%M')
            
            
            

            # Hourly Forecast Chart
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']
            forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric'

            forecast_response = requests.get(forecast_url)
            if forecast_response.status_code == 200:
                forecast_data = forecast_response.json()
                hourly_labels = []
                hourly_temps = []

                for forecast in forecast_data['list'][:8]:  # Next 8 intervals (24 hours, 3-hour gaps)
                    time = forecast['dt_txt'].split(' ')[1][:5]  # Extract only HH:MM
                    temp = forecast['main']['temp']
                    hourly_labels.append(time)
                    hourly_temps.append(temp)

                hourly_chart_data = {
                    'labels': hourly_labels,
                    'values': hourly_temps
                }

    # News API (always fetch)
    try:
        news_api_key = '725b9f9ea4c44c6b8af2871436cd702b'
        if city:
            news_url = f'https://newsapi.org/v2/everything?q={city}&language=en&apiKey={news_api_key}'
        else:
            news_url = f'https://newsapi.org/v2/top-headlines?country=in&category=general&language=en&apiKey={news_api_key}'

        news_response = requests.get(news_url)
        if news_response.status_code == 200:
            articles = news_response.json().get('articles', [])
            news_data = articles[:4]

    except Exception as e:
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
    api_key = '090ccd6c9968e0e7f9bca262bc93b2ee'

    if lat and lon:
        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
        response = requests.get(url)
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': 'Weather not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
