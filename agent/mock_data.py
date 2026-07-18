"""
TripMind AI — Mock Data Engine.

Provides realistic travel data for offline/demo mode when external API keys
are not configured.  Every function returns data that looks and feels like
a real API response so the rest of the application works seamlessly.
"""

import hashlib
import json
import random
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# City coordinates
# ---------------------------------------------------------------------------
CITY_COORDS = {
    'Goa': (15.4909, 73.8278),
    'Kerala': (9.9312, 76.2673),
    'Alleppey': (9.4981, 76.3388),
    'Kochi': (9.9312, 76.2673),
    'Munnar': (10.0889, 77.0595),
    'Manali': (32.2396, 77.1887),
    'Jaipur': (26.9124, 75.7873),
    'Udaipur': (24.5854, 73.7125),
    'Delhi': (28.6139, 77.2090),
    'Mumbai': (19.0760, 72.8777),
    'Bangalore': (12.9716, 77.5946),
    'Chennai': (13.0827, 80.2707),
    'Hyderabad': (17.3850, 78.4867),
    'Kolkata': (22.5726, 88.3639),
    'Varanasi': (25.3176, 82.9739),
    'Rishikesh': (30.0869, 78.2676),
    'Andaman': (11.7401, 92.6586),
    'Ladakh': (34.1526, 77.5771),
    'Leh': (34.1526, 77.5771),
    'Coorg': (12.4244, 75.7382),
    'Mysore': (12.2958, 76.6394),
    'Ooty': (11.4102, 76.6950),
    'Shimla': (31.1048, 77.1734),
    'Darjeeling': (27.0360, 88.2627),
    'Agra': (27.1767, 78.0081),
    'Amritsar': (31.6340, 74.8723),
    'Pune': (18.5204, 73.8567),
    'Srinagar': (34.0837, 74.7973),
    'Port Blair': (11.6234, 92.7265),
}

# ---------------------------------------------------------------------------
# Places database — per destination, per category
# ---------------------------------------------------------------------------
PLACES_DB = {
    'Goa': {
        'beach': [
            {'name': 'Baga Beach', 'kinds': 'beaches,natural', 'rating': 4.3, 'cost_inr': 0, 'description': 'Lively beach famous for water sports and nightlife.'},
            {'name': 'Calangute Beach', 'kinds': 'beaches,natural', 'rating': 4.1, 'cost_inr': 0, 'description': 'Queen of beaches — long stretch of golden sand.'},
            {'name': 'Palolem Beach', 'kinds': 'beaches,natural', 'rating': 4.5, 'cost_inr': 0, 'description': 'Crescent-shaped paradise in South Goa.'},
            {'name': 'Anjuna Beach', 'kinds': 'beaches,natural', 'rating': 4.0, 'cost_inr': 0, 'description': 'Rocky beach with the famous Wednesday flea market.'},
            {'name': 'Vagator Beach', 'kinds': 'beaches,natural', 'rating': 4.2, 'cost_inr': 0, 'description': 'Red cliffs and dramatic views near Chapora Fort.'},
            {'name': 'Colva Beach', 'kinds': 'beaches,natural', 'rating': 4.0, 'cost_inr': 0, 'description': 'Longest beach in South Goa, white sand.'},
            {'name': 'Arambol Beach', 'kinds': 'beaches,natural', 'rating': 4.4, 'cost_inr': 0, 'description': 'Bohemian vibe with drum circles and sweet lake.'},
            {'name': 'Morjim Beach', 'kinds': 'beaches,natural', 'rating': 4.3, 'cost_inr': 0, 'description': 'Turtle nesting site, peaceful and scenic.'},
        ],
        'food': [
            {'name': "Britto's Bar & Restaurant", 'kinds': 'food,restaurants', 'rating': 4.2, 'cost_inr': 600, 'description': 'Iconic Baga beachside seafood shack.'},
            {'name': 'Ritz Classic', 'kinds': 'food,restaurants', 'rating': 4.5, 'cost_inr': 200, 'description': 'Legendary fish thali in Panjim.'},
            {'name': "Martin's Corner", 'kinds': 'food,restaurants', 'rating': 4.4, 'cost_inr': 700, 'description': 'Goan classics in Betalbatim.'},
            {'name': "Fernando's Nostalgia", 'kinds': 'food,restaurants', 'rating': 4.3, 'cost_inr': 400, 'description': 'Pork Vindaloo and Goan sausages.'},
            {'name': "Gunpowder", 'kinds': 'food,restaurants', 'rating': 4.6, 'cost_inr': 800, 'description': 'South Indian fusion in Assagao.'},
        ],
        'general': [
            {'name': 'Basilica of Bom Jesus', 'kinds': 'historic,cultural', 'rating': 4.7, 'cost_inr': 0, 'description': 'UNESCO World Heritage church with St. Francis Xavier relics.'},
            {'name': 'Fort Aguada', 'kinds': 'historic,cultural', 'rating': 4.4, 'cost_inr': 25, 'description': 'Portuguese-era fort with panoramic sea views.'},
            {'name': 'Se Cathedral', 'kinds': 'historic,cultural', 'rating': 4.5, 'cost_inr': 0, 'description': 'One of the largest churches in Asia.'},
            {'name': 'Dudhsagar Falls', 'kinds': 'natural,waterfalls', 'rating': 4.8, 'cost_inr': 600, 'description': "India's tallest tiered waterfall, jeep ride adventure."},
            {'name': 'Spice Plantation Tour', 'kinds': 'cultural,nature', 'rating': 4.3, 'cost_inr': 500, 'description': 'Guided tour with traditional lunch.'},
            {'name': 'Chapora Fort', 'kinds': 'historic', 'rating': 4.2, 'cost_inr': 0, 'description': 'Famous Dil Chahta Hai fort with stunning views.'},
            {'name': 'Fontainhas Latin Quarter', 'kinds': 'cultural,heritage', 'rating': 4.4, 'cost_inr': 0, 'description': 'Colourful Portuguese heritage quarter in Panjim.'},
        ],
    },
    'Kerala': {
        'general': [
            {'name': 'Alleppey Houseboat Cruise', 'kinds': 'water,cultural', 'rating': 4.8, 'cost_inr': 8000, 'description': 'Traditional kettuvallam through palm-fringed backwaters.'},
            {'name': 'Munnar Tea Gardens', 'kinds': 'natural,gardens', 'rating': 4.7, 'cost_inr': 100, 'description': 'Rolling emerald hills of tea plantations.'},
            {'name': 'Periyar Wildlife Sanctuary', 'kinds': 'natural,wildlife', 'rating': 4.5, 'cost_inr': 300, 'description': 'Bamboo rafting and jungle treks for elephants.'},
            {'name': 'Fort Kochi', 'kinds': 'historic,cultural', 'rating': 4.6, 'cost_inr': 0, 'description': 'Chinese fishing nets and colonial heritage.'},
            {'name': 'Kumarakom Bird Sanctuary', 'kinds': 'natural,wildlife', 'rating': 4.3, 'cost_inr': 50, 'description': 'Birdwatching haven on Vembanad Lake.'},
            {'name': 'Kathakali Performance', 'kinds': 'cultural,arts', 'rating': 4.6, 'cost_inr': 300, 'description': 'Classical dance-drama with elaborate makeup.'},
            {'name': 'Kovalam Beach', 'kinds': 'beaches,natural', 'rating': 4.4, 'cost_inr': 0, 'description': 'Lighthouse beach with calm swimming waters.'},
        ],
        'family': [
            {'name': 'Eravikulam National Park', 'kinds': 'natural,wildlife', 'rating': 4.6, 'cost_inr': 125, 'description': 'Home of the endangered Nilgiri Tahr.'},
            {'name': 'Mattupetty Dam', 'kinds': 'natural,scenic', 'rating': 4.2, 'cost_inr': 50, 'description': 'Scenic reservoir surrounded by tea gardens.'},
            {'name': 'Wonderla Kochi', 'kinds': 'amusement', 'rating': 4.5, 'cost_inr': 1200, 'description': 'Premier water and amusement park.'},
            {'name': 'Kerala Folklore Museum', 'kinds': 'museum,cultural', 'rating': 4.4, 'cost_inr': 200, 'description': 'Three-floor museum of Kerala heritage.'},
        ],
    },
    'Manali': {
        'adventure': [
            {'name': 'Solang Valley Paragliding', 'kinds': 'sport,adventure', 'rating': 4.7, 'cost_inr': 2500, 'description': '15-minute tandem flight with Himalayan views.'},
            {'name': 'Beas River Rafting', 'kinds': 'sport,water', 'rating': 4.5, 'cost_inr': 1200, 'description': '14 km Grade II-III rapids from Pirdi.'},
            {'name': 'Rohtang Pass', 'kinds': 'natural,adventure', 'rating': 4.6, 'cost_inr': 500, 'description': 'Snow point at 3,978m with stunning views.'},
            {'name': 'Jogini Falls Trek', 'kinds': 'natural,hiking', 'rating': 4.4, 'cost_inr': 0, 'description': '2-hour hike through apple orchards.'},
            {'name': 'Solang Valley Zorbing', 'kinds': 'sport,adventure', 'rating': 4.0, 'cost_inr': 500, 'description': 'Roll down grassy slopes in a giant ball.'},
            {'name': 'Hampta Pass Trek', 'kinds': 'hiking,adventure', 'rating': 4.8, 'cost_inr': 5000, 'description': 'Multi-day trek crossing dramatic landscapes.'},
        ],
        'general': [
            {'name': 'Hadimba Temple', 'kinds': 'religious,historic', 'rating': 4.6, 'cost_inr': 0, 'description': '1553 wooden shrine in a cedar forest.'},
            {'name': 'Old Manali', 'kinds': 'cultural', 'rating': 4.3, 'cost_inr': 0, 'description': 'Backpacker hub with cafés and shops.'},
            {'name': 'Mall Road Manali', 'kinds': 'shopping', 'rating': 4.0, 'cost_inr': 0, 'description': 'Main shopping street for shawls and handicrafts.'},
            {'name': 'Naggar Castle', 'kinds': 'historic,museum', 'rating': 4.4, 'cost_inr': 15, 'description': 'Medieval castle with Roerich art gallery.'},
            {'name': 'Vashisht Hot Springs', 'kinds': 'natural', 'rating': 4.2, 'cost_inr': 0, 'description': 'Natural sulphur hot springs in stone bath.'},
        ],
    },
    'Jaipur': {
        'general': [
            {'name': 'Amber Fort', 'kinds': 'historic,architecture', 'rating': 4.8, 'cost_inr': 100, 'description': 'Majestic hilltop fort with Sheesh Mahal mirror work.'},
            {'name': 'Hawa Mahal', 'kinds': 'historic,architecture', 'rating': 4.6, 'cost_inr': 50, 'description': 'Iconic Palace of Winds with 953 windows.'},
            {'name': 'City Palace', 'kinds': 'historic,museum', 'rating': 4.7, 'cost_inr': 500, 'description': 'Royal museum with the world\'s largest silver vessels.'},
            {'name': 'Nahargarh Fort', 'kinds': 'historic,scenic', 'rating': 4.5, 'cost_inr': 50, 'description': 'Sunset viewpoint over the Pink City.'},
            {'name': 'Jantar Mantar', 'kinds': 'historic,science', 'rating': 4.4, 'cost_inr': 50, 'description': 'UNESCO World Heritage astronomical observatory.'},
            {'name': 'Johri Bazaar', 'kinds': 'shopping,cultural', 'rating': 4.3, 'cost_inr': 0, 'description': 'Traditional jewellery and Rajasthani crafts.'},
            {'name': 'Albert Hall Museum', 'kinds': 'museum,cultural', 'rating': 4.3, 'cost_inr': 40, 'description': 'Indo-Saracenic architecture housing art and artefacts.'},
        ],
        'honeymoon': [
            {'name': 'Samode Palace', 'kinds': 'heritage,luxury', 'rating': 4.9, 'cost_inr': 12000, 'description': 'Romantic heritage stay with Sheesh Mahal.'},
            {'name': 'Amber Fort Light Show', 'kinds': 'cultural,entertainment', 'rating': 4.5, 'cost_inr': 300, 'description': 'Evening sound and light spectacle.'},
            {'name': 'Hot Air Balloon Ride', 'kinds': 'adventure,romantic', 'rating': 4.7, 'cost_inr': 8000, 'description': 'Sunrise flight over Amer Fort and countryside.'},
        ],
    },
    'Udaipur': {
        'general': [
            {'name': 'City Palace', 'kinds': 'historic,architecture', 'rating': 4.8, 'cost_inr': 300, 'description': "Rajasthan's largest palace with panoramic lake views."},
            {'name': 'Lake Pichola Boat Ride', 'kinds': 'water,scenic', 'rating': 4.7, 'cost_inr': 400, 'description': 'Cruise past Jag Mandir and Lake Palace.'},
            {'name': 'Saheliyon ki Bari', 'kinds': 'garden,historic', 'rating': 4.3, 'cost_inr': 10, 'description': 'Beautiful fountain garden for royal ladies.'},
            {'name': 'Fateh Sagar Lake', 'kinds': 'natural,scenic', 'rating': 4.5, 'cost_inr': 150, 'description': 'Evening walk and pedal boating.'},
            {'name': 'Vintage Car Museum', 'kinds': 'museum', 'rating': 4.2, 'cost_inr': 250, 'description': 'Rare Rolls Royces of the Mewar royals.'},
            {'name': 'Ambrai Restaurant', 'kinds': 'food,scenic', 'rating': 4.6, 'cost_inr': 500, 'description': 'Lakefront dining with palace views.'},
        ],
        'honeymoon': [
            {'name': 'Lake Pichola Sunset Cruise', 'kinds': 'water,romantic', 'rating': 4.9, 'cost_inr': 800, 'description': 'Golden hour cruise past illuminated palaces.'},
            {'name': 'Taj Lake Palace', 'kinds': 'luxury,heritage', 'rating': 5.0, 'cost_inr': 25000, 'description': 'Floating palace hotel — ultimate romance.'},
            {'name': 'Bagore Ki Haveli Dance Show', 'kinds': 'cultural,entertainment', 'rating': 4.5, 'cost_inr': 150, 'description': 'Rajasthani folk dance in a lakeside haveli.'},
        ],
    },
    'Rishikesh': {
        'adventure': [
            {'name': 'Shivpuri River Rafting', 'kinds': 'sport,water', 'rating': 4.7, 'cost_inr': 1200, 'description': '16 km Grade III-IV rapids on the Ganges.'},
            {'name': 'Jumpin Heights Bungee', 'kinds': 'sport,adventure', 'rating': 4.6, 'cost_inr': 3550, 'description': '83m bungee jump — tallest in India.'},
            {'name': 'Beatles Ashram', 'kinds': 'historic,cultural', 'rating': 4.5, 'cost_inr': 600, 'description': 'Abandoned ashram with street art and meditation halls.'},
            {'name': 'Ganga Aarti at Triveni Ghat', 'kinds': 'spiritual', 'rating': 4.8, 'cost_inr': 0, 'description': 'Deeply spiritual evening fire ceremony.'},
            {'name': 'Ram Jhula', 'kinds': 'historic,scenic', 'rating': 4.4, 'cost_inr': 0, 'description': 'Iconic suspension bridge over the Ganges.'},
        ],
        'spiritual': [
            {'name': 'Parmarth Niketan Ashram', 'kinds': 'spiritual,yoga', 'rating': 4.7, 'cost_inr': 500, 'description': 'Daily yoga classes and ashram life.'},
            {'name': 'Ganga Aarti at Triveni Ghat', 'kinds': 'spiritual', 'rating': 4.8, 'cost_inr': 0, 'description': 'Free evening fire ceremony by the river.'},
            {'name': 'Neelkanth Mahadev Temple', 'kinds': 'religious', 'rating': 4.5, 'cost_inr': 0, 'description': 'Ancient Shiva temple in the hills.'},
        ],
    },
    'Varanasi': {
        'spiritual': [
            {'name': 'Dashashwamedh Ghat Aarti', 'kinds': 'spiritual', 'rating': 4.9, 'cost_inr': 0, 'description': 'Spectacular multi-priest fire ceremony.'},
            {'name': 'Kashi Vishwanath Temple', 'kinds': 'religious', 'rating': 4.8, 'cost_inr': 0, 'description': 'One of the 12 Jyotirlingas of Lord Shiva.'},
            {'name': 'Sunrise Boat Ride on Ganges', 'kinds': 'scenic,spiritual', 'rating': 4.7, 'cost_inr': 300, 'description': 'Witness the ancient ghats at dawn.'},
            {'name': 'Sarnath', 'kinds': 'historic,religious', 'rating': 4.6, 'cost_inr': 20, 'description': "Where Buddha gave his first sermon."},
            {'name': 'Assi Ghat', 'kinds': 'cultural,spiritual', 'rating': 4.5, 'cost_inr': 0, 'description': 'Popular ghat with morning rituals and cafés.'},
        ],
        'general': [
            {'name': 'Dashashwamedh Ghat', 'kinds': 'spiritual,scenic', 'rating': 4.9, 'cost_inr': 0, 'description': 'Main ghat with the grand evening aarti.'},
            {'name': 'Banaras Hindu University', 'kinds': 'cultural,educational', 'rating': 4.5, 'cost_inr': 0, 'description': 'Beautiful campus with Vishwanath Temple.'},
            {'name': 'Blue Lassi Shop', 'kinds': 'food', 'rating': 4.7, 'cost_inr': 80, 'description': 'Legendary lassi since 1940.'},
        ],
    },
}

# ---------------------------------------------------------------------------
# Default places for any destination not in PLACES_DB
# ---------------------------------------------------------------------------
DEFAULT_PLACES = [
    {'name': 'City Center Walking Tour', 'kinds': 'cultural,sightseeing', 'rating': 4.2, 'cost_inr': 0, 'description': 'Explore the heart of the city on foot.'},
    {'name': 'Local Heritage Museum', 'kinds': 'museum,cultural', 'rating': 4.0, 'cost_inr': 100, 'description': 'Discover the history and culture of the region.'},
    {'name': 'Main Market & Bazaar', 'kinds': 'shopping', 'rating': 4.1, 'cost_inr': 0, 'description': 'Shop for local crafts, spices, and souvenirs.'},
    {'name': 'Sunset Viewpoint', 'kinds': 'natural,scenic', 'rating': 4.5, 'cost_inr': 0, 'description': 'Best vantage point for golden hour photos.'},
    {'name': 'Local Temple', 'kinds': 'religious,cultural', 'rating': 4.3, 'cost_inr': 0, 'description': 'Beautiful traditional architecture and peaceful atmosphere.'},
    {'name': 'Nature Park', 'kinds': 'natural,park', 'rating': 4.2, 'cost_inr': 50, 'description': 'Green space perfect for morning walks and picnics.'},
]

# ---------------------------------------------------------------------------
# Restaurant templates
# ---------------------------------------------------------------------------
RESTAURANT_TEMPLATES = {
    'Goa': [
        {'name': "Britto's Baga", 'cuisine': 'Goan Seafood', 'cost_inr': 500, 'rating': 4.2},
        {'name': 'Ritz Classic Panjim', 'cuisine': 'Goan Thali', 'cost_inr': 200, 'rating': 4.5},
        {'name': "Gunpowder Assagao", 'cuisine': 'South Indian Fusion', 'cost_inr': 700, 'rating': 4.6},
        {'name': 'Thalassa Vagator', 'cuisine': 'Greek-Goan', 'cost_inr': 1200, 'rating': 4.4},
    ],
    'Jaipur': [
        {'name': 'Padao at Nahargarh', 'cuisine': 'Rajasthani', 'cost_inr': 400, 'rating': 4.3},
        {'name': 'Laxmi Mishthan Bhandar', 'cuisine': 'Sweets & Chaat', 'cost_inr': 150, 'rating': 4.6},
        {'name': '1135 AD Amber Fort', 'cuisine': 'Royal Rajasthani', 'cost_inr': 1500, 'rating': 4.7},
    ],
    'Manali': [
        {'name': 'Lazy Dog Lounge', 'cuisine': 'Café & Pizza', 'cost_inr': 400, 'rating': 4.3},
        {'name': "Drifter's Café", 'cuisine': 'Israeli & Continental', 'cost_inr': 350, 'rating': 4.4},
        {'name': 'Johnson Bar & Restaurant', 'cuisine': 'North Indian', 'cost_inr': 500, 'rating': 4.2},
    ],
}

# ---------------------------------------------------------------------------
# Hotel templates
# ---------------------------------------------------------------------------
HOTEL_TEMPLATES = {
    'Goa': [
        {'name': 'The Leela Goa', 'stars': 5, 'price_inr': 12000, 'rating': 4.7, 'amenities': 'Pool, Spa, Beach Access, Restaurant'},
        {'name': 'Taj Exotica Resort', 'stars': 5, 'price_inr': 15000, 'rating': 4.8, 'amenities': 'Golf Course, Pool, Spa, Fine Dining'},
        {'name': 'Country Inn Candolim', 'stars': 3, 'price_inr': 3500, 'rating': 4.1, 'amenities': 'Pool, Restaurant, Wi-Fi'},
        {'name': 'OYO Beach Retreat', 'stars': 2, 'price_inr': 1200, 'rating': 3.8, 'amenities': 'AC, Wi-Fi, Near Beach'},
    ],
    'Manali': [
        {'name': 'The Himalayan', 'stars': 4, 'price_inr': 6000, 'rating': 4.5, 'amenities': 'Mountain View, Spa, Restaurant'},
        {'name': 'Snow Valley Resorts', 'stars': 3, 'price_inr': 3000, 'rating': 4.2, 'amenities': 'Bonfire, Restaurant, Valley View'},
        {'name': 'Hotel Manali Inn', 'stars': 2, 'price_inr': 1500, 'rating': 3.9, 'amenities': 'AC, Wi-Fi, Room Service'},
    ],
    'Jaipur': [
        {'name': 'Rambagh Palace', 'stars': 5, 'price_inr': 25000, 'rating': 4.9, 'amenities': 'Heritage, Pool, Spa, Fine Dining'},
        {'name': 'ITC Rajputana', 'stars': 5, 'price_inr': 8000, 'rating': 4.6, 'amenities': 'Pool, Spa, Multiple Restaurants'},
        {'name': 'Hotel Pearl Palace', 'stars': 3, 'price_inr': 2000, 'rating': 4.4, 'amenities': 'Rooftop Restaurant, AC, Wi-Fi'},
    ],
}

DEFAULT_HOTELS = [
    {'name': 'Grand Heritage Hotel', 'stars': 4, 'price_inr': 5000, 'rating': 4.3, 'amenities': 'AC, Pool, Restaurant, Wi-Fi'},
    {'name': 'Comfort Inn & Suites', 'stars': 3, 'price_inr': 2500, 'rating': 4.0, 'amenities': 'AC, Wi-Fi, Breakfast'},
    {'name': 'Budget Traveller Lodge', 'stars': 2, 'price_inr': 1000, 'rating': 3.7, 'amenities': 'AC, Wi-Fi'},
]

# ---------------------------------------------------------------------------
# Weather by region and month
# ---------------------------------------------------------------------------
WEATHER_DATA = {
    'Goa': {
        'winter': {'description': 'clear sky', 'temp_c': 28.5, 'humidity': 55, 'rain_warning': False, 'suggestion': 'Light cotton clothes, sunscreen, sunglasses'},
        'summer': {'description': 'hot and humid', 'temp_c': 34.2, 'humidity': 75, 'rain_warning': False, 'suggestion': 'Light breathable clothing, lots of water'},
        'monsoon': {'description': 'heavy rain', 'temp_c': 27.0, 'humidity': 90, 'rain_warning': True, 'suggestion': 'Waterproof jacket, umbrella, quick-dry clothes'},
    },
    'Kerala': {
        'winter': {'description': 'pleasant and warm', 'temp_c': 26.8, 'humidity': 60, 'rain_warning': False, 'suggestion': 'Comfortable cottons, mosquito repellent'},
        'summer': {'description': 'hot and humid', 'temp_c': 33.0, 'humidity': 80, 'rain_warning': False, 'suggestion': 'Light clothes, hat, sunscreen'},
        'monsoon': {'description': 'heavy monsoon rain', 'temp_c': 25.5, 'humidity': 95, 'rain_warning': True, 'suggestion': 'Waterproof gear, umbrella essential'},
    },
    'Manali': {
        'winter': {'description': 'snowfall', 'temp_c': 2.0, 'humidity': 70, 'rain_warning': False, 'suggestion': 'Heavy jacket, thermals, boots, gloves'},
        'summer': {'description': 'pleasant and cool', 'temp_c': 18.5, 'humidity': 50, 'rain_warning': False, 'suggestion': 'Layered clothing, light jacket for evenings'},
        'monsoon': {'description': 'moderate rain', 'temp_c': 16.0, 'humidity': 85, 'rain_warning': True, 'suggestion': 'Rain jacket, waterproof shoes'},
    },
    'Jaipur': {
        'winter': {'description': 'cool and dry', 'temp_c': 15.0, 'humidity': 35, 'rain_warning': False, 'suggestion': 'Light jacket for mornings, comfortable walking shoes'},
        'summer': {'description': 'extremely hot', 'temp_c': 42.0, 'humidity': 20, 'rain_warning': False, 'suggestion': 'Light loose cotton, hat, sunscreen, lots of water'},
        'monsoon': {'description': 'warm with rain showers', 'temp_c': 30.0, 'humidity': 70, 'rain_warning': True, 'suggestion': 'Umbrella, light rain jacket'},
    },
    'Udaipur': {
        'winter': {'description': 'pleasant and cool', 'temp_c': 16.5, 'humidity': 30, 'rain_warning': False, 'suggestion': 'Light sweater for evenings, comfortable casuals'},
        'summer': {'description': 'very hot', 'temp_c': 40.0, 'humidity': 25, 'rain_warning': False, 'suggestion': 'Light clothes, hat, stay hydrated'},
        'monsoon': {'description': 'warm with occasional showers', 'temp_c': 28.0, 'humidity': 65, 'rain_warning': True, 'suggestion': 'Light rain jacket, umbrella'},
    },
    'Rishikesh': {
        'winter': {'description': 'cold mornings, pleasant days', 'temp_c': 12.0, 'humidity': 45, 'rain_warning': False, 'suggestion': 'Warm layers, walking shoes'},
        'summer': {'description': 'warm and humid', 'temp_c': 32.0, 'humidity': 60, 'rain_warning': False, 'suggestion': 'Quick-dry clothes for rafting, sunscreen'},
        'monsoon': {'description': 'heavy rain, river floods', 'temp_c': 26.0, 'humidity': 90, 'rain_warning': True, 'suggestion': 'Avoid rafting, waterproof gear required'},
    },
    'Varanasi': {
        'winter': {'description': 'foggy and cool', 'temp_c': 13.0, 'humidity': 60, 'rain_warning': False, 'suggestion': 'Warm clothes, walking shoes for ghats'},
        'summer': {'description': 'extremely hot', 'temp_c': 40.5, 'humidity': 30, 'rain_warning': False, 'suggestion': 'Light cotton, hat, lots of water'},
        'monsoon': {'description': 'very humid with rain', 'temp_c': 30.0, 'humidity': 85, 'rain_warning': True, 'suggestion': 'Umbrella, quick-dry clothes'},
    },
}

DEFAULT_WEATHER = {
    'winter': {'description': 'pleasant weather', 'temp_c': 22.0, 'humidity': 50, 'rain_warning': False, 'suggestion': 'Comfortable clothes, light layers'},
    'summer': {'description': 'warm and sunny', 'temp_c': 35.0, 'humidity': 40, 'rain_warning': False, 'suggestion': 'Light cotton clothes, sunscreen, hat'},
    'monsoon': {'description': 'rain showers expected', 'temp_c': 27.0, 'humidity': 80, 'rain_warning': True, 'suggestion': 'Umbrella, waterproof shoes'},
}

# ---------------------------------------------------------------------------
# Flight templates
# ---------------------------------------------------------------------------
AIRLINES = ['IndiGo', 'Air India', 'SpiceJet', 'Vistara', 'Go First', 'AirAsia India', 'Akasa Air']

FLIGHT_ROUTES = {
    ('Delhi', 'Goa'): {'duration': '2h 35m', 'base_fare': 4500},
    ('Mumbai', 'Goa'): {'duration': '1h 15m', 'base_fare': 3200},
    ('Bangalore', 'Goa'): {'duration': '1h 20m', 'base_fare': 3500},
    ('Delhi', 'Jaipur'): {'duration': '1h 05m', 'base_fare': 3000},
    ('Mumbai', 'Jaipur'): {'duration': '1h 55m', 'base_fare': 4000},
    ('Delhi', 'Kerala'): {'duration': '3h 10m', 'base_fare': 5500},
    ('Mumbai', 'Kerala'): {'duration': '1h 50m', 'base_fare': 4200},
    ('Delhi', 'Manali'): {'duration': '1h 30m', 'base_fare': 4800},
    ('Delhi', 'Udaipur'): {'duration': '1h 20m', 'base_fare': 3800},
    ('Mumbai', 'Udaipur'): {'duration': '1h 35m', 'base_fare': 4200},
    ('Delhi', 'Varanasi'): {'duration': '1h 25m', 'base_fare': 3500},
    ('Delhi', 'Rishikesh'): {'duration': '0h 55m', 'base_fare': 3200},
    ('Delhi', 'Ladakh'): {'duration': '1h 25m', 'base_fare': 6500},
    ('Delhi', 'Srinagar'): {'duration': '1h 30m', 'base_fare': 5000},
    ('Mumbai', 'Delhi'): {'duration': '2h 10m', 'base_fare': 4000},
    ('Bangalore', 'Delhi'): {'duration': '2h 45m', 'base_fare': 5000},
    ('Chennai', 'Delhi'): {'duration': '2h 40m', 'base_fare': 4800},
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _get_season(month: int = 0) -> str:
    """Return 'winter', 'summer', or 'monsoon' based on month."""
    if not month:
        month = datetime.now().month
    if month in (11, 12, 1, 2):
        return 'winter'
    elif month in (3, 4, 5, 6):
        return 'summer'
    else:
        return 'monsoon'


def _seed_random(text: str):
    """Seed random generator from text for deterministic but varied output."""
    h = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    random.seed(h)


def _make_maps_url(city: str, place_name: str = '') -> str:
    """Generate an OpenStreetMap URL for a city / place."""
    lat, lon = CITY_COORDS.get(city, (20.5937, 78.9629))
    # Add small deterministic offset per place
    if place_name:
        _seed_random(place_name)
        lat += random.uniform(-0.02, 0.02)
        lon += random.uniform(-0.02, 0.02)
    return f'https://www.openstreetmap.org/?mlat={lat:.4f}&mlon={lon:.4f}&zoom=16'


# ===================================================================
# PUBLIC API: functions called by the mock-aware agent layer
# ===================================================================

def mock_geocode(city: str) -> tuple:
    """Return (lat, lon) for a city from the local database."""
    return CITY_COORDS.get(city, (20.5937, 78.9629))


def mock_fetch_places(destination: str, category: str) -> list:
    """Return a list of place dicts for destination + category."""
    dest_data = PLACES_DB.get(destination, {})
    places = dest_data.get(category, dest_data.get('general', DEFAULT_PLACES))

    result = []
    for p in places:
        result.append({
            'name': p['name'],
            'kinds': p.get('kinds', ''),
            'rating': p.get('rating', 4.0),
            'maps_url': _make_maps_url(destination, p['name']),
        })
    return result


def mock_get_weather(destination: str, month: int = 0) -> dict:
    """Return mock weather data based on destination and season."""
    season = _get_season(month)
    city_weather = WEATHER_DATA.get(destination, DEFAULT_WEATHER)
    if isinstance(city_weather, dict) and 'winter' in city_weather:
        data = city_weather.get(season, city_weather.get('winter'))
    else:
        data = DEFAULT_WEATHER.get(season)
    return {
        'description': data['description'],
        'temp_c': data['temp_c'],
        'humidity': data.get('humidity', 50),
        'rain_warning': data['rain_warning'],
        'suggestion': data.get('suggestion', 'Pack comfortable clothes.'),
    }


def mock_get_flights(origin: str, destination: str) -> list:
    """Generate realistic mock flight data."""
    route = FLIGHT_ROUTES.get((origin, destination))
    if not route:
        # Generate generic flight data
        route = {'duration': '2h 00m', 'base_fare': 4500}

    _seed_random(f'{origin}-{destination}')
    flights = []
    times = ['06:15', '08:30', '10:45', '14:20', '17:55', '20:10']
    for i in range(min(5, len(times))):
        airline = AIRLINES[i % len(AIRLINES)]
        fare = route['base_fare'] + random.randint(-500, 1500)
        flights.append({
            'airline': airline,
            'flight_number': f'{airline[:2].upper()}{random.randint(100, 999)}',
            'departure': times[i],
            'duration': route['duration'],
            'fare_inr': max(fare, 2000),
            'origin': origin,
            'destination': destination,
        })
    random.seed()  # Reset
    return flights


def mock_get_hotels(destination: str) -> list:
    """Return mock hotel data for a destination."""
    hotels = HOTEL_TEMPLATES.get(destination, DEFAULT_HOTELS)
    result = []
    for h in hotels:
        result.append({
            'name': h['name'],
            'stars': h.get('stars', 3),
            'price_inr': h['price_inr'],
            'rating': h['rating'],
            'amenities': h.get('amenities', 'AC, Wi-Fi'),
            'address': f'{h["name"]}, {destination}',
            'available': True,
        })
    return result


def mock_extract_intent(user_message: str, prev_state: dict) -> dict:
    """
    Extract trip intent from a user message using pattern matching.
    No LLM required. Returns updated state fields.
    """
    msg = user_message.lower()
    state = dict(prev_state)

    # Destination detection
    for city in CITY_COORDS:
        if city.lower() in msg:
            state['destination'] = city
            break

    # Number of days
    day_patterns = [
        r'(\d+)[\s-]*(?:day|days|night|nights)',
        r'(\d+)[\s-]*d\b',
    ]
    for pattern in day_patterns:
        m = re.search(pattern, msg)
        if m:
            state['num_days'] = int(m.group(1))
            break

    # Budget
    budget_patterns = [
        r'(?:budget|₹|inr|rs\.?)\s*(\d[\d,]*)\s*k?\b',
        r'(\d[\d,]*)\s*(?:k|K|thousand)',
        r'(\d{4,})',  # Numbers 4+ digits likely budget
    ]
    for pattern in budget_patterns:
        m = re.search(pattern, msg)
        if m:
            val = int(m.group(1).replace(',', ''))
            if val < 1000:
                val *= 1000  # "60k" → 60000
            state['budget_inr'] = val
            break

    # Category
    category_keywords = {
        'beach': ['beach', 'sea', 'ocean', 'coast', 'surf'],
        'adventure': ['adventure', 'trek', 'trekking', 'hiking', 'rafting', 'paraglid', 'bungee'],
        'family': ['family', 'kids', 'children', 'kid-friendly'],
        'honeymoon': ['honeymoon', 'romantic', 'couple', 'romance'],
        'food': ['food', 'cuisine', 'culinary', 'eat', 'restaurant', 'foodie'],
        'spiritual': ['spiritual', 'temple', 'religious', 'pilgrimage', 'meditation', 'yoga'],
    }
    for cat, keywords in category_keywords.items():
        if any(kw in msg for kw in keywords):
            state['category'] = cat
            break

    # Group size
    group_m = re.search(r'(\d+)\s*(?:people|person|pax|traveller|member)', msg)
    if group_m:
        state['group_size'] = int(group_m.group(1))

    # Origin city
    origin_phrases = [r'from\s+(\w+)', r'departing\s+(\w+)', r'leaving\s+(\w+)']
    for pattern in origin_phrases:
        m = re.search(pattern, msg)
        if m:
            origin = m.group(1).capitalize()
            if origin in CITY_COORDS and origin != state.get('destination', ''):
                state['origin_city'] = origin
                break

    # Start Date
    date_patterns = [
        r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s+\d{4})?)',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}/\d{1,2}/\d{4})'
    ]
    for pattern in date_patterns:
        m = re.search(pattern, msg)
        if m:
            state['start_date'] = m.group(1)
            break
            
    if not state.get('start_date'):
        import datetime
        state['start_date'] = (datetime.date.today() + datetime.timedelta(days=30)).strftime('%Y-%m-%d')

    # Hotel Preference
    hotel_m = re.search(r'(hotels?\s+(?:near|close to|by|with)[\w\s]+?(?=\b(?:in|at|for|on)\b|$))', msg)
    if hotel_m:
        state['hotel_pref'] = hotel_m.group(1).strip()
    else:
        hotel_m2 = re.search(r'(\b(?:cheap|luxury|beachfront|budget|5-star|3-star|boutique)\b\s+(?:hotels?|resorts?))', msg)
        if hotel_m2:
            state['hotel_pref'] = hotel_m2.group(1).strip()

    return state


def mock_build_itinerary(destination: str, num_days: int, category: str,
                         budget_inr: int, group_size: int, places: list) -> list:
    """
    Build a realistic day-by-day itinerary without any LLM.
    Returns the same JSON structure that the Gemini-based builder would produce.
    """
    _seed_random(f'{destination}-{num_days}-{category}')

    dest_data = PLACES_DB.get(destination, {})
    cat_places = dest_data.get(category, dest_data.get('general', DEFAULT_PLACES))
    all_places = cat_places + dest_data.get('general', DEFAULT_PLACES) if category != 'general' else cat_places

    # Also use the places from tools/mock if provided
    if places:
        for p in places:
            if p not in all_places and isinstance(p, dict):
                all_places.append(p)

    # Restaurants
    restaurants = RESTAURANT_TEMPLATES.get(destination, [
        {'name': f'Local Restaurant ({destination})', 'cuisine': 'Regional', 'cost_inr': 400, 'rating': 4.0},
        {'name': f'Street Food Market ({destination})', 'cuisine': 'Street Food', 'cost_inr': 150, 'rating': 4.2},
        {'name': f'Fine Dining ({destination})', 'cuisine': 'Multi-Cuisine', 'cost_inr': 1000, 'rating': 4.5},
    ])

    # Day titles
    day_titles = {
        'beach': ['Beach Bliss & Waves', 'Coastal Adventures', 'Sun, Sand & Seafood', 'Island Hopping', 'Sunset Paradise'],
        'adventure': ['Adrenaline Rush', 'Mountain Thrills', 'Wild & Free', 'Peak Expedition', 'Trail Blazing'],
        'family': ['Fun Together', 'Family Discovery', 'Explore & Play', 'Memory Making', 'Joy Ride'],
        'honeymoon': ['Romance Begins', 'Love & Luxury', 'Couples Retreat', 'Starlit Evening', 'Forever Memories'],
        'food': ['Flavour Trail', 'Culinary Discovery', 'Street to Fine', 'Spice Route', 'Taste of the City'],
        'spiritual': ['Inner Peace', 'Sacred Journey', 'Temple Trail', 'Mindful Morning', 'Soul Searching'],
        'general': ['City Exploration', 'Heritage Walk', 'Culture Dive', 'Hidden Gems', 'Grand Finale'],
    }
    titles = day_titles.get(category, day_titles['general'])

    itinerary = []
    place_idx = 0

    for day in range(1, num_days + 1):
        title = titles[(day - 1) % len(titles)]
        if num_days > 1:
            if day == 1:
                title = f'Arrival & {title}'
            elif day == num_days:
                title = f'{title} & Departure'

        slots = []

        # Breakfast
        rest = restaurants[day % len(restaurants)]
        slots.append({
            'start_time': '08:30',
            'end_time': '09:30',
            'place': rest['name'],
            'type': 'meal',
            'cost_inr': rest.get('cost_inr', 300) // 2,
            'notes': f'Breakfast — {rest.get("cuisine", "Local")} cuisine',
            'maps_url': _make_maps_url(destination, rest['name']),
        })

        # Morning activity (2 slots)
        for t_start, t_end in [('09:45', '11:30'), ('11:45', '13:00')]:
            if place_idx < len(all_places):
                p = all_places[place_idx]
                place_idx += 1
            else:
                place_idx = 0
                p = all_places[place_idx]
                place_idx += 1

            slots.append({
                'start_time': t_start,
                'end_time': t_end,
                'place': p['name'],
                'type': 'sightseeing' if 'historic' in p.get('kinds', '') or 'cultural' in p.get('kinds', '') else 'activity',
                'cost_inr': p.get('cost_inr', 0),
                'notes': p.get('description', 'Explore this local attraction.'),
                'maps_url': p.get('maps_url', _make_maps_url(destination, p['name'])),
            })

        # Lunch
        lunch_rest = restaurants[(day + 1) % len(restaurants)]
        slots.append({
            'start_time': '13:00',
            'end_time': '14:00',
            'place': lunch_rest['name'],
            'type': 'meal',
            'cost_inr': lunch_rest.get('cost_inr', 400),
            'notes': f'Lunch — {lunch_rest.get("cuisine", "Regional")} speciality',
            'maps_url': _make_maps_url(destination, lunch_rest['name']),
        })

        # Transit
        slots.append({
            'start_time': '14:00',
            'end_time': '14:30',
            'place': f'Travel to next attraction',
            'type': 'transit',
            'cost_inr': random.choice([50, 100, 150, 200, 300]),
            'notes': 'Auto-rickshaw or taxi ride',
            'maps_url': '',
        })

        # Afternoon activity
        if place_idx < len(all_places):
            p = all_places[place_idx]
            place_idx += 1
        else:
            place_idx = 0
            p = all_places[0]

        slots.append({
            'start_time': '14:30',
            'end_time': '17:00',
            'place': p['name'],
            'type': 'activity',
            'cost_inr': p.get('cost_inr', 0),
            'notes': p.get('description', 'Afternoon exploration.'),
            'maps_url': p.get('maps_url', _make_maps_url(destination, p['name'])),
        })

        # Evening activity
        if place_idx < len(all_places):
            p = all_places[place_idx]
            place_idx += 1
        else:
            p = {'name': f'{destination} Evening Walk', 'cost_inr': 0, 'description': 'Relaxing evening stroll through the city.'}

        slots.append({
            'start_time': '17:30',
            'end_time': '19:30',
            'place': p['name'],
            'type': 'activity',
            'cost_inr': p.get('cost_inr', 0),
            'notes': p.get('description', 'Evening exploration.'),
            'maps_url': p.get('maps_url', _make_maps_url(destination, p['name'])),
        })

        # Dinner
        dinner_rest = restaurants[(day + 2) % len(restaurants)]
        slots.append({
            'start_time': '20:00',
            'end_time': '21:00',
            'place': dinner_rest['name'],
            'type': 'meal',
            'cost_inr': dinner_rest.get('cost_inr', 600),
            'notes': f'Dinner — {dinner_rest.get("cuisine", "Local")} dinner experience',
            'maps_url': _make_maps_url(destination, dinner_rest['name']),
        })

        itinerary.append({
            'day': day,
            'title': title,
            'slots': slots,
        })

    random.seed()  # Reset
    return itinerary
