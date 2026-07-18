"""
TripMind AI — External API tool functions.

Provides geocoding, place search (OpenTripMap), weather forecasts
(OpenWeatherMap), and flight look-ups (AviationStack).  All network
calls are wrapped in try/except with logging and sensible fallbacks.

**Mock-aware**: Each function automatically falls back to the
corresponding mock data function when its API key is missing or
set to a placeholder value.  No user configuration needed.
"""

import json
import logging
import os
from functools import lru_cache

import requests

from .mock_data import (
    mock_geocode,
    mock_fetch_places,
    mock_get_weather,
    mock_get_flights,
)

logger = logging.getLogger('agent')

# ---------------------------------------------------------------------------
# API keys (loaded once from environment)
# ---------------------------------------------------------------------------
OTM_KEY: str = os.environ.get('OTM_KEY', '')
ORS_KEY: str = os.environ.get('ORS_KEY', '')
OWM_KEY: str = os.environ.get('OWM_KEY', '')
AVI_KEY: str = os.environ.get('AVI_KEY', '')
SERPAPI_KEY: str = os.environ.get('SERPAPI_KEY', '')

HEADERS = {'User-Agent': 'TripMindAI/1.0'}

_PLACEHOLDER_KEYS = {'', 'your-api-key-here', 'CHANGE_ME', 'your_api_key'}

# ---------------------------------------------------------------------------
# Log which functions will use mock mode at startup
# ---------------------------------------------------------------------------
_mock_status: list[str] = []
if not SERPAPI_KEY or SERPAPI_KEY in _PLACEHOLDER_KEYS:
    _mock_status.append('fetch_places (SERPAPI_KEY missing)')
if not OWM_KEY or OWM_KEY in _PLACEHOLDER_KEYS:
    _mock_status.append('get_weather (OWM_KEY missing)')
if not AVI_KEY or AVI_KEY in _PLACEHOLDER_KEYS:
    _mock_status.append('get_flight_data (AVI_KEY missing)')

if _mock_status:
    logger.warning(
        'Tools: Mock mode active for: %s', ', '.join(_mock_status)
    )
else:
    logger.info('Tools: All API keys configured — using live APIs.')

# ---------------------------------------------------------------------------
# Static look-up tables
# ---------------------------------------------------------------------------
CITY_TO_IATA: dict[str, str] = {
    'Mumbai': 'BOM',
    'Delhi': 'DEL',
    'Bangalore': 'BLR',
    'Goa': 'GOI',
    'Chennai': 'MAA',
    'Hyderabad': 'HYD',
    'Kolkata': 'CCU',
    'Pune': 'PNQ',
    'Kochi': 'COK',
    'Jaipur': 'JAI',
    'Ahmedabad': 'AMD',
    'Srinagar': 'SXR',
    'Leh': 'IXL',
    'Port Blair': 'IXZ',
    'Varanasi': 'VNS',
    'Amritsar': 'ATQ',
    'Chandigarh': 'IXC',
    'Lucknow': 'LKO',
    'Bhopal': 'BHO',
    'Indore': 'IDR',
}

CATEGORY_MAP: dict[str, str] = {
    'beach': 'natural,beaches,water',
    'adventure': 'natural,sport,other_parks_and_outdoor_areas',
    'family': 'amusements,museums,cultural',
    'food': 'foods,restaurants,cafes',
    'spiritual': 'religion,historic',
    'honeymoon': 'natural,cultural,historic',
    'general': 'interesting_places,cultural,natural',
}


# ---------------------------------------------------------------------------
# 1. Geocode a city via Nominatim
# ---------------------------------------------------------------------------
@lru_cache(maxsize=200)
def geocode_city(city: str) -> tuple[float, float]:
    """Return ``(lat, lon)`` for *city* using the Nominatim geocoder.

    Falls back to the geographic centre of India ``(20.5937, 78.9629)``
    on any error.  Uses ``mock_geocode()`` when network is unavailable.
    """
    try:
        resp = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': city, 'format': 'json', 'limit': 1},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return (float(data[0]['lat']), float(data[0]['lon']))
        logger.warning(f'Nominatim returned empty result for "{city}"')
    except Exception as e:
        logger.warning(
            f'Geocode error for "{city}": {e} — falling back to mock data.'
        )
        return mock_geocode(city)

    return (20.5937, 78.9629)


# ---------------------------------------------------------------------------
# 2. Fetch places from SerpApi (Google Local)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=200)
def fetch_places(destination: str, category: str) -> tuple[str, ...]:
    """Fetch up to 15 place details for *destination* / *category*.

    Returns a **tuple of JSON strings** (one per place) so the result is
    hashable for ``lru_cache``.

    Falls back to ``mock_fetch_places()`` when ``SERPAPI_KEY`` is missing.
    """
    if not SERPAPI_KEY or SERPAPI_KEY in _PLACEHOLDER_KEYS:
        logger.info(
            f'[MOCK] fetch_places("{destination}", "{category}") — '
            f'SERPAPI_KEY not set, using mock data.'
        )
        mock_places = mock_fetch_places(destination, category)
        return tuple(json.dumps(p) for p in mock_places)

    try:
        search_query = f"{category} attractions in {destination}"
        if category == 'food':
            search_query = f"best restaurants in {destination}"
        elif category == 'shopping':
            search_query = f"shopping markets in {destination}"
            
        resp = requests.get(
            'https://serpapi.com/search',
            params={
                'engine': 'google_local',
                'q': search_query,
                'location': destination,
                'api_key': SERPAPI_KEY,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        local_results = data.get('local_results', [])
        places: list[str] = []
        for item in local_results[:15]:
            name = item.get('title', '').strip()
            if not name:
                continue

            gps = item.get('gps_coordinates', {})
            lat = gps.get('latitude', 0)
            lon = gps.get('longitude', 0)

            maps_url = item.get('links', {}).get('directions')
            if not maps_url and lat and lon:
                 maps_url = f'https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=16'
            
            place_dict = {
                'name': name,
                'kinds': item.get('type', category),
                'rating': item.get('rating', 0),
                'maps_url': maps_url or '',
            }
            places.append(json.dumps(place_dict))

        return tuple(places)

    except Exception as e:
        logger.error(f'fetch_places (SerpApi) error for "{destination}": {e}')
        return ()


# ---------------------------------------------------------------------------
# 3. Weather forecast from OpenWeatherMap
# ---------------------------------------------------------------------------
def get_weather(destination: str, date_str: str = '') -> dict:
    """Return a compact weather summary for *destination*.

    Returns
    -------
    dict
        ``{'description': str, 'temp_c': float, 'rain_warning': bool}``
        or an empty dict on failure.

    Falls back to ``mock_get_weather()`` when ``OWM_KEY`` is missing.
    """
    # Mock fallback — key missing or placeholder
    if not OWM_KEY or OWM_KEY in _PLACEHOLDER_KEYS:
        logger.info(
            f'[MOCK] get_weather("{destination}") — '
            f'OWM_KEY not set, using mock data.'
        )
        mock_data = mock_get_weather(destination)
        # Return same dict format as the real implementation
        return {
            'description': mock_data['description'],
            'temp_c': mock_data['temp_c'],
            'rain_warning': mock_data['rain_warning'],
        }

    # Real mode — OpenWeatherMap API
    try:
        resp = requests.get(
            'https://api.openweathermap.org/data/2.5/forecast',
            params={
                'q': destination,
                'appid': OWM_KEY,
                'units': 'metric',
                'cnt': 8,
            },
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        forecasts = data.get('list', [])
        if not forecasts:
            return {}

        # Pick the closest forecast entry to the requested date, or the
        # first entry if no date was specified.
        entry = forecasts[0]
        if date_str:
            for fc in forecasts:
                if date_str in fc.get('dt_txt', ''):
                    entry = fc
                    break

        weather_main = entry.get('weather', [{}])[0]
        description = weather_main.get('description', 'N/A')
        temp_c = entry.get('main', {}).get('temp', 0.0)

        # Rain warning: true if any forecast slot mentions "rain"
        rain_warning = any(
            'rain' in fc.get('weather', [{}])[0].get('main', '').lower()
            for fc in forecasts
        )

        return {
            'description': description,
            'temp_c': round(temp_c, 1),
            'rain_warning': rain_warning,
        }

    except Exception as e:
        logger.error(f'Weather error for "{destination}": {e}')
        return {}


# ---------------------------------------------------------------------------
# 4. Flight data from AviationStack
# ---------------------------------------------------------------------------
def get_flight_data(origin: str, destination: str) -> list[dict]:
    """Return up to 5 scheduled flights from *origin* → *destination*.

    Requires ``AVI_KEY`` to be set; falls back to ``mock_get_flights()``
    when the key is missing.
    """
    # Mock fallback — key missing or placeholder
    if not AVI_KEY or AVI_KEY in _PLACEHOLDER_KEYS:
        logger.info(
            f'[MOCK] get_flight_data("{origin}", "{destination}") — '
            f'AVI_KEY not set, using mock data.'
        )
        return mock_get_flights(origin, destination)

    # Real mode — AviationStack API
    dep_iata = CITY_TO_IATA.get(origin, '')
    arr_iata = CITY_TO_IATA.get(destination, '')
    if not dep_iata or not arr_iata:
        logger.warning(
            f'IATA code missing: origin="{origin}" → "{dep_iata}", '
            f'destination="{destination}" → "{arr_iata}"'
        )
        return []

    try:
        resp = requests.get(
            'http://api.aviationstack.com/v1/flights',
            params={
                'access_key': AVI_KEY,
                'dep_iata': dep_iata,
                'arr_iata': arr_iata,
                'flight_status': 'scheduled',
                'limit': 5,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('data', [])

    except Exception as e:
        logger.error(f'Flight data error ({origin} → {destination}): {e}')
        return []
