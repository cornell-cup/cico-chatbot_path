'''
This file calls a weather API and a geocoding API (getting latitude and
longitude coordinates)
'''

import requests
import geocoder

BASE_ONE_DAY = "http://api.openweathermap.org/data/2.5/weather?"
BASE_FIVE_DAY = "http://api.openweathermap.org/data/2.5/forecast?"
KEY = "APPID="
LAT = "lat="
LNG = "lon="
UNITS = "units="

GEONAMES_USERNAME = ""

def lookup_weather_today(lat, lng):
    '''
    Looks up the current day's forcast for a certain coordinate
    location

    @param lat: a string for the latitude
    @param lng: a string for the longitude

    @return: the full json data from the API call
    '''

    r = requests.get(BASE_ONE_DAY+KEY+"&"+LAT+lat+"&"+LNG+lng+"&"
            +UNITS+"imperial")
    return r.json()

def lookup_weather_today_city(city):
    '''
    Convenience function that converts city name into lat, lng.
    Calls lookup_weather_today() and returns output

    @param city: city name. Should include more specific info as needed (country, state, etc.).
    If empty string, returns empty string

    @return: if valid city is specified, the full json data from the API call.
        Otherwise empty string
    '''
    if city == "":
        return ""
    
    lat, lng = city_to_coord(city)
    
    if lat == None and lng == None:
        return ""
    return lookup_weather_today(lat, lng)

def lookup_weather_five_day(lat, lng):
    '''
    Looks up the five day forcast for a certain coordinate
    location

    @param lat: a string for the latitude
    @param lng: a string for the longitude

    @return: the full json data from the API call
    '''

    r = requests.get(BASE_FIVE_DAY+KEY+"&"+LAT+lat+"&"+LNG+lng)
    return r.json()

def import_keys():
    '''
    Imports all of the necessary API keys
    '''

    global KEY, GEONAMES_USERNAME

    #geonames API
    with open("api_keys/geonames_username.txt") as f:
        GEONAMES_USERNAME = f.read().strip()

    #openweather API
    with open("api_keys/open_weather.txt") as f:
        KEY = KEY + f.read().strip()

def city_to_coord(city_string):
    '''
    Geocodes a city name into latitude, longitude coordinates

    @param city_string: the name of the city

    @return: A tuple with (latitude, longitude). If the city name
        is not valid, then (None, None)
    '''

    g = geocoder.geonames(city_string, key=GEONAMES_USERNAME)
    
    if g.code == None:
        return (None, None)
    return (g.lat, g.lng)

import_keys()

if __name__ == "__main__":
    import json

    #coords = city_to_coord("ithaca new york")
    coords = city_to_coord("weather today")
    print(coords)

    #forecast = lookup_weather_today(coords[0], coords[1])
    #print(json.dumps(forecast))
