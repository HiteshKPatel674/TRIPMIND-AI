"""
Destination Knowledge Hub Service
Aggregates rich information about a destination from multiple sources.
"""
import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Static reference data for Indian destinations ─────────────────────────
DESTINATION_FACTS = {
    'default': {
        'currency': 'Indian Rupee (₹)',
        'language': 'Hindi, English',
        'timezone': 'IST (UTC+5:30)',
        'emergency': '112 (Unified Emergency), 100 (Police), 108 (Ambulance)',
        'country_code': '+91',
        'electricity': '230V, 50Hz (Type C/D/M plugs)',
        'water': 'Drink bottled water only',
        'tipping': '10-15% at restaurants',
    },
    'goa': {
        'language': 'Konkani, English, Hindi',
        'best_season': 'November to February',
        'local_tips': 'Rent a scooter for beach hopping. Avoid monsoon (June-Sept) for beach activities.',
        'transport': 'Scooter/bike rental, auto-rickshaws, local buses. No Uber in most areas.',
        'known_for': 'Beaches, Portuguese architecture, seafood, nightlife, water sports',
    },
    'jaipur': {
        'language': 'Hindi, Rajasthani, English',
        'best_season': 'October to March',
        'local_tips': 'Bargain at markets. Visit forts early morning to avoid heat.',
        'transport': 'Auto-rickshaws, Ola/Uber, city buses. Negotiate auto fares beforehand.',
        'known_for': 'Pink City, forts, palaces, handicrafts, Rajasthani cuisine',
    },
    'delhi': {
        'language': 'Hindi, English, Punjabi',
        'best_season': 'October to March',
        'local_tips': 'Use Delhi Metro for major attractions. Street food at Chandni Chowk is legendary.',
        'transport': 'Metro (best option), Ola/Uber, auto-rickshaws, DTC buses.',
        'known_for': 'Mughal architecture, street food, shopping, historical monuments',
    },
    'mumbai': {
        'language': 'Marathi, Hindi, English',
        'best_season': 'November to February',
        'local_tips': 'Take a local train during off-peak hours for the authentic Mumbai experience.',
        'transport': 'Local trains, BEST buses, Ola/Uber, auto-rickshaws (suburbs only).',
        'known_for': 'Bollywood, street food, Marine Drive, nightlife, colonial architecture',
    },
    'kerala': {
        'language': 'Malayalam, English',
        'best_season': 'September to March',
        'local_tips': 'Book houseboat early in season. Try Sadhya (traditional feast) on banana leaf.',
        'transport': 'KSRTC buses, auto-rickshaws, boats in backwaters, taxi.',
        'known_for': "Backwaters, Ayurveda, tea plantations, wildlife, 'God's Own Country'",
    },
    'manali': {
        'language': 'Hindi, Pahari',
        'best_season': 'March to June, December to February (snow)',
        'local_tips': 'Carry warm layers even in summer. Rohtang Pass needs advance permit.',
        'transport': 'Local taxis, auto-rickshaws, Volvo buses from Delhi (12-14 hrs).',
        'known_for': 'Snow, adventure sports, Solang Valley, temples, hippie culture',
    },
    'varanasi': {
        'language': 'Hindi, Bhojpuri',
        'best_season': 'October to March',
        'local_tips': 'Attend Ganga Aarti at Dashashwamedh Ghat. Take a dawn boat ride.',
        'transport': 'Auto-rickshaws, cycle-rickshaws, boats. Walking is best in old city.',
        'known_for': 'Ganges ghats, spirituality, silk weaving, street food, ancient temples',
    },
    'udaipur': {
        'language': 'Hindi, Mewari, English',
        'best_season': 'September to March',
        'local_tips': 'Sunset boat ride on Lake Pichola is unmissable. Rooftop dining is magical.',
        'transport': 'Auto-rickshaws, Ola/Uber, walking in old city.',
        'known_for': "Lakes, palaces, romantic ambiance, 'Venice of the East'",
    },
    'meghalaya': {
        'language': 'Khasi, Garo, English',
        'best_season': 'October to May',
        'local_tips': 'Living root bridges need 1-3 hour treks. Carry rain gear always.',
        'transport': 'Shared taxis, private cabs. Limited public transport.',
        'known_for': 'Living root bridges, cleanest village (Mawlynnong), waterfalls, caves',
    },
    'ladakh': {
        'language': 'Ladakhi, Hindi, English',
        'best_season': 'June to September',
        'local_tips': 'Acclimatize for 1-2 days in Leh before high-altitude trips.',
        'transport': 'Rented bikes/cars, shared taxis. Inner Line Permit needed for some areas.',
        'known_for': 'Pangong Lake, monasteries, high-altitude passes, stark landscapes',
    },
    'rajasthan': {
        'language': 'Hindi, Rajasthani, English',
        'best_season': 'October to March',
        'local_tips': 'Stay in heritage havelis for authentic experience. Carry sunscreen.',
        'transport': 'Trains between cities, auto-rickshaws within cities.',
        'known_for': 'Forts, palaces, desert safaris, colorful culture, handicrafts',
    },
    'kashmir': {
        'language': 'Kashmiri, Urdu, Hindi',
        'best_season': 'March to October',
        'local_tips': 'Stay on a houseboat in Dal Lake. Try Wazwan cuisine.',
        'transport': 'Shikaras, taxis, local buses. Airport in Srinagar.',
        'known_for': "Dal Lake, Mughal gardens, snow, houseboats, 'Paradise on Earth'",
    },
    'rishikesh': {
        'language': 'Hindi, English',
        'best_season': 'September to November, February to May',
        'local_tips': 'Book river rafting in advance. Respect the alcohol-free zone.',
        'transport': 'Auto-rickshaws, shared taxis, walking. No Uber.',
        'known_for': 'Yoga capital, river rafting, adventure sports, Beatles Ashram',
    },
    'shimla': {
        'language': 'Hindi, Pahari, English',
        'best_season': 'March to June, December to February (snow)',
        'local_tips': 'Walk the Mall Road and Ridge. Toy train from Kalka is iconic.',
        'transport': 'Local taxis, walking (Mall Road is pedestrian). Toy train.',
        'known_for': 'Colonial architecture, Mall Road, Toy Train, scenic views',
    },
}


def _get_city_facts(destination: str) -> Dict[str, str]:
    """Get static facts for a destination."""
    dest_lower = destination.lower().strip()
    facts = dict(DESTINATION_FACTS['default'])

    for key, city_facts in DESTINATION_FACTS.items():
        if key == 'default':
            continue
        if key in dest_lower or dest_lower in key:
            facts.update(city_facts)
            break

    return facts


def get_wikipedia_summary(destination: str) -> str:
    """Fetch destination summary from Wikipedia REST API (server-side)."""
    try:
        encoded = urllib.parse.quote(destination)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'TripMindAI/2.0 (travel planner app)',
        })
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data and data.get('extract'):
                return data['extract']
    except Exception as e:
        logger.warning(f"Wikipedia fetch failed for {destination}: {e}")

    return f"{destination} is a beautiful destination in India, rich in culture, history and natural beauty. It offers a unique travel experience that blends traditional charm with modern comforts."


class DestinationInfoService:
    """Aggregates rich destination information from multiple sources."""

    def get_info(self, destination: str, category: str = 'general') -> Dict[str, Any]:
        """
        Returns a comprehensive destination info dict with:
        - summary: Wikipedia description
        - facts: Quick reference facts (currency, language, etc.)
        - best_season, local_tips, transport, known_for: City-specific info
        """
        facts = _get_city_facts(destination)
        summary = get_wikipedia_summary(destination)

        return {
            'summary': summary,
            'currency': facts.get('currency', 'Indian Rupee (₹)'),
            'language': facts.get('language', 'Hindi, English'),
            'timezone': facts.get('timezone', 'IST (UTC+5:30)'),
            'emergency': facts.get('emergency', '112'),
            'country_code': facts.get('country_code', '+91'),
            'electricity': facts.get('electricity', '230V, 50Hz'),
            'water': facts.get('water', 'Drink bottled water'),
            'tipping': facts.get('tipping', '10-15%'),
            'best_season': facts.get('best_season', 'October to March'),
            'local_tips': facts.get('local_tips', f'Explore {destination} with an open mind and comfortable shoes!'),
            'transport': facts.get('transport', 'Auto-rickshaws, taxis, and local buses are widely available.'),
            'known_for': facts.get('known_for', f'{destination} is known for its unique culture, history, and natural beauty.'),
        }
