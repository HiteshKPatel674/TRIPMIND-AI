import datetime
import random

def _generate_time(hour_start: int, hour_end: int) -> str:
    h = random.randint(hour_start, hour_end)
    m = random.choice([0, 15, 30, 45])
    return f"{h:02d}:{m:02d}"

def _add_duration(time_str: str, duration_hours: int, duration_mins: int) -> tuple[str, int]:
    h, m = map(int, time_str.split(':'))
    m += duration_mins
    h += duration_hours + (m // 60)
    m = m % 60
    days_added = h // 24
    h = h % 24
    return f"{h:02d}:{m:02d}", days_added

def get_mock_trains(origin: str, dest: str, target_date: datetime.date) -> list:
    random.seed(f"trains-{origin}-{dest}")
    trains = []
    
    types = [
        ("Rajdhani Express", 24, [('1A', 4000), ('2A', 2800), ('3A', 2100)]),
        ("Shatabdi Express", 12, [('EC', 2500), ('CC', 1200)]),
        ("Vande Bharat", 10, [('EC', 3000), ('CC', 1500)]),
        ("Duronto Express", 26, [('1A', 3800), ('2A', 2600), ('3A', 2000), ('SL', 700)]),
        ("Superfast Express", 30, [('2A', 2200), ('3A', 1600), ('SL', 550), ('2S', 300)]),
        ("Mail/Express", 36, [('2A', 2000), ('3A', 1400), ('SL', 500), ('2S', 250)])
    ]
    
    # Generate ~20 trains
    for i in range(25):
        t_type, base_dur, classes = random.choice(types)
        num = random.randint(11000, 22999)
        name = f"{origin[:3].upper()} {dest[:3].upper()} {t_type}"
        
        # Randomize duration slightly (-10% to +10%)
        actual_dur = base_dur + random.uniform(-0.1 * base_dur, 0.1 * base_dur)
        dur_h = int(actual_dur)
        dur_m = int((actual_dur - dur_h) * 60)
        
        dep_time = _generate_time(0, 23)
        arr_time, days = _add_duration(dep_time, dur_h, dur_m)
        
        arr_date = target_date + datetime.timedelta(days=days)
        
        classes = [('1A', 4500), ('2A', 3000), ('3A', 2200), ('SL', 900)]
        
        train_num = str(random.randint(10000, 99999))
        
        trains.append({
            'id': train_num,
            'name': f"{origin.capitalize()} {dest.capitalize()} Express",
            'number': train_num,
            'train_type': random.choice(['EXP', 'SF', 'RAJDHANI', 'SHATABDI']),
            'source_station_name': origin.capitalize(),
            'source_station_code': origin[:3].upper(),
            'dest_station_name': dest.capitalize(),
            'dest_station_code': dest[:3].upper(),
            'departure_time': dep_time,
            'arrival_time': arr_time,
            'departure_date': target_date.strftime('%Y-%m-%d'),
            'arrival_date': arr_date.strftime('%Y-%m-%d'),
            'duration_str': f"{dur_h}h {dur_m}m",
            'duration_hours': actual_dur,
            'stops': random.randint(2, 15),
            'days_of_running': 'Daily',
            'availability': f"Available {random.randint(10, 150)}" if random.random() > 0.3 else f"WL {random.randint(1, 50)}",
            'classes': [{'name': c[0], 'price': c[1] + random.randint(-100, 100)} for c in classes],
            'cheapest_price': min([c[1] for c in classes]) + random.randint(-100, 100),
            'is_direct': random.choice([True, True, True, False])
        })
        
    random.seed()
    return sorted(trains, key=lambda x: x['duration_hours'])

def get_mock_flights(origin: str, dest: str, target_date: datetime.date) -> list:
    random.seed(f"flights-{origin}-{dest}")
    flights = []
    airlines = ["IndiGo", "Air India", "Vistara", "Akasa Air", "SpiceJet"]
    
    base_dur_h = 2
    base_dur_m = 15
    base_price = 4500
    
    for i in range(15):
        airline = random.choice(airlines)
        is_direct = random.random() > 0.4
        
        if is_direct:
            dur_h, dur_m = base_dur_h, base_dur_m + random.randint(-15, 30)
            stops = "Non-stop"
            price = base_price + random.randint(0, 3000)
        else:
            dur_h = base_dur_h + random.randint(1, 5)
            dur_m = random.randint(0, 59)
            stops = "1 Stop"
            price = base_price - random.randint(500, 1500)
            
        dep_time = _generate_time(4, 22)
        arr_time, days = _add_duration(dep_time, dur_h, dur_m)
        arr_date = target_date + datetime.timedelta(days=days)
        
        flights.append({
            'id': f"{airline[:2].upper()}-{random.randint(100,999)}",
            'airline': airline,
            'departure_time': dep_time,
            'arrival_time': arr_time,
            'departure_date': target_date.strftime('%Y-%m-%d'),
            'arrival_date': arr_date.strftime('%Y-%m-%d'),
            'duration_str': f"{dur_h}h {dur_m}m",
            'duration_hours': dur_h + (dur_m / 60.0),
            'stops': stops,
            'price': price,
            'baggage': "15kg Check-in, 7kg Cabin"
        })
        
    random.seed()
    return sorted(flights, key=lambda x: x['price'])

def get_mock_buses(origin: str, dest: str, target_date: datetime.date) -> list:
    random.seed(f"buses-{origin}-{dest}")
    buses = []
    operators = ["VRL Travels", "SRS Travels", "Orange Tours", "KSRTC", "IntrCity SmartBus"]
    types = [
        ("A/C Sleeper (2+1)", 1200),
        ("Volvo Multi-Axle A/C Semi Sleeper", 1000),
        ("Non A/C Sleeper", 800),
        ("Non A/C Seater", 500)
    ]
    
    base_dur = 14
    
    for i in range(10):
        operator = random.choice(operators)
        b_type, price = random.choice(types)
        
        dur_h = base_dur + random.randint(-2, 4)
        dur_m = random.choice([0, 15, 30, 45])
        
        # Buses mostly leave in the evening
        dep_time = _generate_time(17, 23)
        arr_time, days = _add_duration(dep_time, dur_h, dur_m)
        arr_date = target_date + datetime.timedelta(days=days)
        
        buses.append({
            'id': f"BUS-{random.randint(1000,9999)}",
            'operator': operator,
            'type': b_type,
            'departure_time': dep_time,
            'arrival_time': arr_time,
            'departure_date': target_date.strftime('%Y-%m-%d'),
            'arrival_date': arr_date.strftime('%Y-%m-%d'),
            'duration_str': f"{dur_h}h {dur_m}m",
            'duration_hours': dur_h + (dur_m / 60.0),
            'price': price + random.randint(-150, 150)
        })
        
    random.seed()
    return sorted(buses, key=lambda x: x['price'])

def get_mock_hotels(dest: str, checkin: datetime.date, checkout: datetime.date) -> list:
    random.seed(f"hotels-{dest}")
    hotels = []
    
    adjectives = ["Grand", "Royal", "Palm", "Sea View", "Mountain", "Valley", "Heritage", "Blue",
                   "Golden", "Silver", "Emerald", "Sunset", "Lakeside", "Hilltop"]
    suffixes = ["Resort", "Hotel", "Inn", "Suites", "Retreat", "Palace", "Boutique Stay", "Villa"]
    
    amenity_pool = {
        5: ["Free WiFi", "Pool", "Spa", "Breakfast Included", "Gym", "Bar", "Room Service", "Airport Shuttle", "Concierge", "Valet Parking"],
        4: ["Free WiFi", "Pool", "Breakfast Included", "Gym", "Restaurant", "Parking", "Laundry", "Room Service"],
        3: ["Free WiFi", "Breakfast Included", "Parking", "Restaurant", "Laundry", "AC Rooms"],
        2: ["Free WiFi", "AC Rooms", "Parking", "Housekeeping"],
    }
    
    reasons = [
        "Best rated by travelers",
        "Budget-friendly pick",
        "Closest to main attractions",
        "Excellent reviews for cleanliness",
        "Great value for amenities",
        "Top choice for families",
        "Romantic getaway pick",
        "Best rooftop views",
        "Walking distance to landmarks",
        "Highly recommended by locals",
    ]
    
    import urllib.parse
    
    for i in range(20):
        adj = random.choice(adjectives)
        suf = random.choice(suffixes)
        name = f"The {adj} {suf}"
        stars = random.choices([5, 4, 3, 2], weights=[10, 30, 40, 20])[0]
        base_price = {5: 12000, 4: 6000, 3: 3000, 2: 1200}[stars]
        price = base_price + random.randint(-500, 2000)
        rating = round(random.uniform(3.5, 4.9), 1)
        
        # Unique AI-generated image per hotel
        img_prompt = urllib.parse.quote(
            f"Professional hotel photography of {name} in {dest} India, "
            f"luxury {stars} star hotel exterior and lobby, "
            f"beautiful architecture, golden hour, 8k quality"
        )
        image_url = f"https://image.pollinations.ai/prompt/{img_prompt}?width=600&height=400&nologo=true"
        
        # Unique booking URL per hotel
        hotel_search = urllib.parse.quote(f"{name} {dest}")
        book_url = (
            f"https://www.booking.com/searchresults.html"
            f"?ss={hotel_search}"
            f"&checkin={checkin.strftime('%Y-%m-%d')}"
            f"&checkout={checkout.strftime('%Y-%m-%d')}"
            f"&group_adults=2&no_rooms=1"
        )
        
        # Google Maps URL
        maps_query = urllib.parse.quote(f"{name} hotel {dest} India")
        maps_url = f"https://www.google.com/maps/search/{maps_query}"
        
        # Pick amenities based on star rating
        available_amenities = amenity_pool.get(stars, amenity_pool[3])
        hotel_amenities = random.sample(available_amenities, min(random.randint(3, 6), len(available_amenities)))
        
        hotels.append({
            'id': f"HOTEL-{random.randint(10000,99999)}",
            'name': name,
            'stars': stars,
            'price_per_night': price,
            'rating': rating,
            'reviews': random.randint(50, 2000),
            'amenities': hotel_amenities,
            'image_placeholder': image_url,
            'book_url': book_url,
            'maps_url': maps_url,
            'recommendation_reason': random.choice(reasons),
        })
        
    random.seed()
    return sorted(hotels, key=lambda x: x['rating'], reverse=True)

