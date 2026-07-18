import datetime
import urllib.parse
from core.models import Trip
from .mock_transport import get_mock_trains, get_mock_flights, get_mock_buses

class BaseTransportProvider:
    def search(self, origin: str, dest: str, start_date: datetime.date):
        raise NotImplementedError

class RailwayProvider(BaseTransportProvider):
    STATION_MAP = {
        'goa': 'MAO',
        'north goa': 'THVM',
        'panaji': 'KRMI',
        'vasco': 'VSG',
        'bangalore': 'SBC',
        'bengaluru': 'SBC',
        'delhi': 'NDLS',
        'new delhi': 'NDLS',
        'mumbai': 'BCT',
        'chennai': 'MAS',
        'kolkata': 'HWH',
        'hyderabad': 'SC',
        'pune': 'PUNE'
    }

    def search(self, origin: str, dest: str, start_date: datetime.date):
        import os
        rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        rapidapi_host = os.environ.get('RAPIDAPI_HOST', 'irctc1.p.rapidapi.com')
        
        origin_code = self.STATION_MAP.get(origin.lower(), origin[:3].upper())
        dest_code = self.STATION_MAP.get(dest.lower(), dest[:3].upper())
        
        if rapidapi_key:
            try:
                return self._get_rapidapi_trains(origin, dest, origin_code, dest_code, start_date, rapidapi_key, rapidapi_host)
            except Exception as e:
                print(f"RapidAPI IRCTC Error: {e}")
                
        # Fallback to mock
        trains = []
        trains.extend(get_mock_trains(origin, dest, start_date - datetime.timedelta(days=2)))
        trains.extend(get_mock_trains(origin, dest, start_date - datetime.timedelta(days=1)))
        trains.extend(get_mock_trains(origin, dest, start_date))
        
        valid_trains = []
        for t in trains:
            # Must arrive on or before start_date 12:00 PM
            arr_d = datetime.datetime.strptime(t['arrival_date'], '%Y-%m-%d').date()
            if arr_d < start_date or (arr_d == start_date and int(t['arrival_time'].split(':')[0]) <= 12):
                t['provider'] = 'irctc'
                date_str = t['departure_date'].replace('-', '')
                t['book_url'] = f"https://www.ixigo.com/search/result/train/{origin_code}/{dest_code}/{date_str}//1/0/0/0/0"
                valid_trains.append(t)
        
        # Deduplicate by ID
        seen = set()
        res = []
        for t in valid_trains:
            if t['id'] not in seen:
                seen.add(t['id'])
                res.append(t)
        
        return sorted(res, key=lambda x: x['duration_hours'])

    def _get_rapidapi_trains(self, origin, dest, origin_code, dest_code, start_date, api_key, api_host):
        import requests
        import random
        
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': api_host
        }
        
        target_dates = [start_date - datetime.timedelta(days=1), start_date]
        all_trains = []
        
        for d in target_dates:
            date_str = d.strftime('%Y-%m-%d')
            params = {
                'fromStationCode': origin_code,
                'toStationCode': dest_code,
                'dateOfJourney': date_str
            }
            try:
                response = requests.get(f"https://{api_host}/api/v3/trainBetweenStations", headers=headers, params=params, timeout=15)
                data = response.json()
                if data.get('status') and data.get('data'):
                    for t in data['data']:
                        train_id = t.get('train_number', str(random.randint(10000, 99999)))
                        dur_str = t.get('duration', '12:00')
                        try:
                            dh, dm = map(int, dur_str.split(':'))
                        except:
                            dh, dm = 12, 0
                            
                        # Mock Fares per class since API doesn't provide them here
                        class_types = t.get('class_type', ['SL', '3A', '2A'])
                        classes = []
                        base_fare = dh * 40
                        for ct in class_types:
                            price = base_fare
                            if ct in ['3A', 'CC']: price = int(base_fare * 2.5)
                            elif ct in ['2A', 'EC']: price = int(base_fare * 3.5)
                            elif ct == '1A': price = int(base_fare * 5.0)
                            elif ct == '2S': price = int(base_fare * 0.6)
                            
                            classes.append({'name': ct, 'price': price + random.randint(-50, 50)})
                            
                        if not classes:
                            classes = [{'name': 'SL', 'price': base_fare}]
                            
                        # Parse days of running
                        run_days = t.get('run_days', [])
                        
                        all_trains.append({
                            'id': train_id,
                            'name': t.get('train_name', 'Express'),
                            'number': train_id,
                            'train_type': t.get('train_type', 'EXP'),
                            'source_station_name': t.get('from_station_name', origin),
                            'source_station_code': t.get('train_src', origin_code),
                            'dest_station_name': t.get('to_station_name', dest),
                            'dest_station_code': t.get('train_dstn', dest_code),
                            'departure_time': t.get('from_std', '00:00'),
                            'arrival_time': t.get('to_sta', '00:00'),
                            'departure_date': date_str,
                            'arrival_date': date_str, # Simplification, need actual logic if overnight
                            'duration_str': f"{dh}h {dm}m",
                            'duration_hours': dh + (dm / 60.0),
                            'stops': t.get('halt_stn', random.randint(2, 10)),
                            'days_of_running': ', '.join(run_days) if run_days else 'Daily',
                            'availability': f"Available {random.randint(10, 150)}" if random.random() > 0.3 else f"WL {random.randint(1, 50)}",
                            'classes': classes,
                            'cheapest_price': min([c['price'] for c in classes]),
                            'is_direct': True,
                            'provider': 'irctc',
                            'book_url': f"https://www.ixigo.com/search/result/train/{origin_code}/{dest_code}/{date_str.replace('-','')}//1/0/0/0/0"
                        })
            except Exception as e:
                print(f"Error fetching date {date_str}: {e}")
                
        # Deduplicate
        seen = set()
        res = []
        for t in all_trains:
            if t['id'] not in seen:
                seen.add(t['id'])
                res.append(t)
                
        if not res:
            raise Exception("No trains found in RapidAPI response")
            
        return sorted(res, key=lambda x: x['duration_hours'])

class FlightProvider(BaseTransportProvider):
    AIRPORT_MAP = {
        'Bangalore': 'BLR',
        'Goa': 'GOI',
        'Delhi': 'DEL',
        'Mumbai': 'BOM',
        'Chennai': 'MAA',
        'Kolkata': 'CCU',
        'Hyderabad': 'HYD',
        'Pune': 'PNQ'
    }

    def search(self, origin: str, dest: str, start_date: datetime.date):
        import os
        serpapi_key = os.environ.get('SERPAPI_KEY')
        if serpapi_key:
            try:
                return self._get_serpapi_flights(origin, dest, start_date, serpapi_key)
            except Exception as e:
                print(f"SerpApi Flights Error: {e}")
                
        # Fallback to mock
        flights = []
        flights.extend(get_mock_flights(origin, dest, start_date - datetime.timedelta(days=1)))
        flights.extend(get_mock_flights(origin, dest, start_date))
        
        valid_flights = []
        for f in flights:
            arr_d = datetime.datetime.strptime(f['arrival_date'], '%Y-%m-%d').date()
            if arr_d < start_date or (arr_d == start_date and int(f['arrival_time'].split(':')[0]) <= 12):
                f['provider'] = 'mmt'
                date_mmt = datetime.datetime.strptime(f['departure_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
                f['book_url'] = f"https://www.makemytrip.com/flight/search?itinerary={origin[:3].upper()}-{dest[:3].upper()}-{date_mmt}&tripType=O&paxType=A-1_C-0_I-0&intl=false"
                valid_flights.append(f)
                
        seen = set()
        res = []
        for f in valid_flights:
            if f['id'] not in seen:
                seen.add(f['id'])
                res.append(f)
                
        return sorted(res, key=lambda x: x['price'])
        
    def _get_serpapi_flights(self, origin: str, dest: str, start_date: datetime.date, api_key: str):
        import requests
        
        # Determine target date for flights (departing on start_date)
        dep_date = start_date.strftime('%Y-%m-%d')
        
        dep_code = self.AIRPORT_MAP.get(origin, origin[:3].upper())
        arr_code = self.AIRPORT_MAP.get(dest, dest[:3].upper())
        
        params = {
            "engine": "google_flights",
            "departure_id": dep_code,
            "arrival_id": arr_code,
            "outbound_date": dep_date,
            "currency": "INR",
            "hl": "en",
            "api_key": api_key
        }
        
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        data = response.json()
        
        best_flights = data.get("best_flights", [])
        other_flights = data.get("other_flights", [])
        all_flights = best_flights + other_flights
        
        if not all_flights:
            raise Exception("No flights returned from SerpApi")
            
        results = []
        for f in all_flights:
            flights_data = f.get('flights', [{}])
            main_flight = flights_data[0]
            
            airline = main_flight.get('airline', 'Airline')
            flight_num = main_flight.get('flight_number', '123')
            
            dep_time = main_flight.get('departure_airport', {}).get('time', '00:00')
            arr_time = flights_data[-1].get('arrival_airport', {}).get('time', '00:00')
            
            # Extract time string like '2026-07-15 10:00' -> '10:00'
            if len(dep_time) > 10:
                dep_time_str = dep_time[-5:]
            else:
                dep_time_str = "00:00"
                
            if len(arr_time) > 10:
                arr_time_str = arr_time[-5:]
            else:
                arr_time_str = "00:00"
            
            dur = f.get('total_duration', 120)
            dur_h = dur // 60
            dur_m = dur % 60
            
            price = f.get('price', 5000)
            
            results.append({
                'id': f"{airline[:2].upper()}-{flight_num}",
                'airline': airline,
                'departure_time': dep_time_str,
                'arrival_time': arr_time_str,
                'departure_date': dep_date,
                'arrival_date': dep_date, # simplifying
                'duration_str': f"{dur_h}h {dur_m}m",
                'duration_hours': dur_h + (dur_m / 60.0),
                'stops': "Non-stop" if len(flights_data) == 1 else f"{len(flights_data)-1} Stop",
                'price': price,
                'book_url': f"https://www.google.com/travel/flights?q=Flights%20to%20{dest}%20from%20{origin}%20on%20{dep_date}"
            })
            
        return sorted(results, key=lambda x: x['price'])

class BusProvider(BaseTransportProvider):
    def search(self, origin: str, dest: str, start_date: datetime.date):
        buses = []
        buses.extend(get_mock_buses(origin, dest, start_date - datetime.timedelta(days=1)))
        buses.extend(get_mock_buses(origin, dest, start_date))
        
        valid_buses = []
        for b in buses:
            arr_d = datetime.datetime.strptime(b['arrival_date'], '%Y-%m-%d').date()
            if arr_d < start_date or (arr_d == start_date and int(b['arrival_time'].split(':')[0]) <= 12):
                b['provider'] = 'redbus'
                date_rb = datetime.datetime.strptime(b['departure_date'], '%Y-%m-%d').strftime('%d-%b-%Y')
                b['book_url'] = f"https://www.redbus.in/bus-tickets/{origin.lower()}-to-{dest.lower()}?fromCityName={origin}&toCityName={dest}&onward={date_rb}"
                valid_buses.append(b)
                
        seen = set()
        res = []
        for b in valid_buses:
            if b['id'] not in seen:
                seen.add(b['id'])
                res.append(b)
                
        return sorted(res, key=lambda x: x['price'])

class RecommendationEngine:
    def get_best_train(self, trains):
        if not trains: return None
        # Balance duration and price
        # Cheapest that is reasonably fast
        sorted_by_price = sorted(trains, key=lambda x: x['cheapest_price'])
        cheapest = sorted_by_price[0]
        fastest = sorted(trains, key=lambda x: x['duration_hours'])[0]
        
        best = fastest
        reason = f"Taking {best['name']} on {best['departure_date']} is recommended because it is the fastest option ({best['duration_str']}) and arrives before your itinerary begins."
        
        if cheapest['id'] != fastest['id'] and (cheapest['duration_hours'] - fastest['duration_hours']) < 4:
            best = cheapest
            reason = f"Taking {best['name']} on {best['departure_date']} is recommended because it saves money while only taking a bit longer ({best['duration_str']})."
            
        best['recommendation_reason'] = reason
        return best

    def get_best_flight(self, flights):
        if not flights: return None
        fastest = sorted(flights, key=lambda x: x['duration_hours'])[0]
        cheapest = sorted(flights, key=lambda x: x['price'])[0]
        
        best = cheapest
        reason = f"Flight {best['airline']} ({best['id']}) is the best value option at ₹{best['price']}."
        
        if fastest['id'] != cheapest['id']:
            price_diff = fastest['price'] - cheapest['price']
            dur_diff = cheapest['duration_hours'] - fastest['duration_hours']
            if price_diff < 1500 and dur_diff > 2:
                best = fastest
                reason = f"Flight {best['airline']} ({best['id']}) is recommended because it is only ₹{price_diff} more than the cheapest option but saves {int(dur_diff)} hours."
                
        best['recommendation_reason'] = reason
        return best

class TransportService:
    def __init__(self):
        self.rail = RailwayProvider()
        self.flight = FlightProvider()
        self.bus = BusProvider()
        self.engine = RecommendationEngine()
        
    def get_recommendations(self, trip: Trip) -> dict:
        origin = trip.origin_city
        dest = trip.destination
        
        # Parse start_date or default to +30 days
        if trip.start_date:
            try:
                if isinstance(trip.start_date, str):
                    start_date = datetime.datetime.strptime(trip.start_date, '%Y-%m-%d').date()
                else:
                    start_date = trip.start_date
            except Exception:
                start_date = datetime.date.today() + datetime.timedelta(days=30)
        else:
            start_date = datetime.date.today() + datetime.timedelta(days=30)

        results = {
            'trains': [],
            'best_train': None,
            'flights': [],
            'best_flight': None,
            'buses': [],
            'origin': origin,
            'dest': dest,
            'start_date': start_date
        }
        
        if origin and origin.lower() != dest.lower():
            trains = self.rail.search(origin, dest, start_date)
            results['trains'] = trains[:10]  # Top 10
            results['best_train'] = self.engine.get_best_train(trains)
            
            flights = self.flight.search(origin, dest, start_date)
            results['flights'] = flights[:10]
            results['best_flight'] = self.engine.get_best_flight(flights)
            
            buses = self.bus.search(origin, dest, start_date)
            results['buses'] = buses[:10]
            
        return results
