from urllib.parse import urlencode, quote_plus

CITY_TO_IATA = {
    'Mumbai': 'BOM', 'Delhi': 'DEL', 'Bangalore': 'BLR', 'Goa': 'GOI',
    'Chennai': 'MAA', 'Hyderabad': 'HYD', 'Kolkata': 'CCU', 'Pune': 'PNQ',
    'Kochi': 'COK', 'Jaipur': 'JAI', 'Ahmedabad': 'AMD', 'Srinagar': 'SXR',
    'Leh': 'IXL', 'Port Blair': 'IXZ', 'Varanasi': 'VNS', 'Amritsar': 'ATQ',
    'Chandigarh': 'IXC', 'Lucknow': 'LKO', 'Bhopal': 'BHO', 'Indore': 'IDR',
}


def get_flight_link(origin: str, destination: str, date_str: str = '') -> str:
    origin_iata = CITY_TO_IATA.get(origin, 'DEL')
    dest_iata = CITY_TO_IATA.get(destination, 'GOI')
    params = urlencode({
        'source': origin_iata,
        'destination': dest_iata,
        'dateofdeparture': date_str.replace('-', ''),
        'adults': '1',
        'class': 'E',
    })
    return f'https://www.goibibo.com/flights/search/?{params}'


def get_hotel_link(destination: str, checkin: str = '', checkout: str = '') -> str:
    params = urlencode({
        'ss': destination,
        'checkin': checkin,
        'checkout': checkout,
        'group_adults': '2',
        'no_rooms': '1',
    })
    return f'https://www.booking.com/searchresults.html?{params}'


def get_train_link(origin: str, destination: str, date_str: str = '') -> str:
    o = quote_plus(origin)
    d = quote_plus(destination)
    return f'https://www.irctc.co.in/nget/train-search?from={o}&to={d}'
