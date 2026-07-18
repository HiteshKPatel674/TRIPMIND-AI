import os
import urllib.request
import urllib.parse
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ── Destination landmarks for context-aware image queries ────────────────
DESTINATION_LANDMARKS = {
    'goa': ['Baga Beach', 'Basilica of Bom Jesus', 'Dudhsagar Falls', 'Fort Aguada', 'Anjuna Flea Market'],
    'jaipur': ['Hawa Mahal', 'Amber Fort', 'City Palace Jaipur', 'Jantar Mantar', 'Nahargarh Fort'],
    'delhi': ['India Gate', 'Red Fort Delhi', 'Qutub Minar', 'Lotus Temple', 'Humayun Tomb'],
    'mumbai': ['Gateway of India', 'Marine Drive Mumbai', 'Chhatrapati Shivaji Terminus', 'Juhu Beach'],
    'kerala': ['Alleppey Houseboat Backwaters', 'Munnar Tea Plantations', 'Kovalam Beach', 'Periyar Wildlife'],
    'manali': ['Rohtang Pass', 'Solang Valley', 'Hadimba Temple', 'Old Manali'],
    'varanasi': ['Dashashwamedh Ghat', 'Kashi Vishwanath Temple', 'Ganges River Aarti'],
    'udaipur': ['Lake Pichola', 'City Palace Udaipur', 'Jag Mandir', 'Lake Palace Hotel'],
    'rishikesh': ['Ram Jhula', 'Laxman Jhula', 'Ganges River Rafting', 'Beatles Ashram'],
    'shimla': ['The Ridge Shimla', 'Mall Road Shimla', 'Christ Church Shimla', 'Kufri'],
    'darjeeling': ['Tiger Hill', 'Darjeeling Himalayan Railway', 'Tea Gardens Darjeeling'],
    'meghalaya': ['Living Root Bridges Meghalaya', 'Dawki River', 'Nohkalikai Falls', 'Shillong Peak'],
    'ladakh': ['Pangong Lake', 'Khardung La Pass', 'Thiksey Monastery', 'Magnetic Hill'],
    'rajasthan': ['Mehrangarh Fort Jodhpur', 'Thar Desert Jaisalmer', 'Pushkar Lake', 'Hawa Mahal Jaipur'],
    'kashmir': ['Dal Lake Srinagar', 'Gulmarg Gondola', 'Pahalgam Valley', 'Mughal Gardens'],
    'andaman': ['Radhanagar Beach Havelock', 'Cellular Jail Port Blair', 'Scuba Diving Andaman'],
    'ooty': ['Botanical Garden Ooty', 'Ooty Lake', 'Nilgiri Mountain Railway', 'Doddabetta Peak'],
    'mysore': ['Mysore Palace', 'Chamundi Hill', 'Brindavan Gardens', 'St Philomena Church'],
    'agra': ['Taj Mahal', 'Agra Fort', 'Fatehpur Sikri', 'Mehtab Bagh'],
    'amritsar': ['Golden Temple Amritsar', 'Wagah Border Ceremony', 'Jallianwala Bagh'],
    'hampi': ['Virupaksha Temple Hampi', 'Stone Chariot Hampi', 'Hampi Ruins'],
    'coorg': ['Abbey Falls Coorg', 'Raja Seat Coorg', 'Coffee Plantations Coorg'],
    'pondicherry': ['Promenade Beach Pondicherry', 'Auroville', 'French Quarter Pondicherry'],
    'jodhpur': ['Mehrangarh Fort', 'Blue City Jodhpur', 'Umaid Bhawan Palace', 'Clock Tower Jodhpur'],
    'jaisalmer': ['Jaisalmer Fort', 'Sam Sand Dunes', 'Patwon Ki Haveli', 'Gadisar Lake'],
}

CATEGORY_THEMES = {
    'beach': 'tropical beach coastline ocean waves sunset',
    'adventure': 'mountain trekking adventure landscape',
    'family': 'scenic family-friendly attractions parks',
    'honeymoon': 'romantic luxury sunset scenic couples',
    'food': 'local cuisine street food traditional restaurant',
    'spiritual': 'temple sacred heritage ancient architecture',
    'general': 'scenic landscape travel iconic landmark',
}


def get_landmark_query(destination: str, category: str = 'general') -> str:
    """Build a landmark-specific search query for accurate destination images."""
    dest_lower = destination.lower().strip()

    # Find matching landmarks
    landmark = None
    for key, landmarks in DESTINATION_LANDMARKS.items():
        if key in dest_lower or dest_lower in key:
            landmark = landmarks[0]  # Use the most iconic landmark
            break

    theme = CATEGORY_THEMES.get(category, CATEGORY_THEMES['general'])

    if landmark:
        return f"{landmark} {destination} India {theme}"
    else:
        return f"Famous landmark {destination} India {theme} iconic scenic"


def get_gallery_queries(destination: str, category: str = 'general') -> List[str]:
    """Generate multiple queries for a destination gallery."""
    dest_lower = destination.lower().strip()
    queries = []

    # Find landmarks
    landmarks = []
    for key, lms in DESTINATION_LANDMARKS.items():
        if key in dest_lower or dest_lower in key:
            landmarks = lms[:5]
            break

    if landmarks:
        for lm in landmarks:
            queries.append(f"{lm} {destination} India")
    else:
        queries = [
            f"Famous landmark {destination} India scenic",
            f"Aerial view {destination} India cityscape",
            f"Local cuisine food {destination} India",
            f"Cultural festival {destination} India",
            f"Nature landscape {destination} India beautiful",
        ]

    return queries


class ImageProvider(ABC):
    def __init__(self, name: str, timeout: int = 3):
        self.name = name
        self.timeout = timeout

    @abstractmethod
    def fetch_image(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        """Returns {'url': str, 'provider': str, 'attribution': str, 'license': str}"""
        pass


class UnsplashProvider(ImageProvider):
    def __init__(self, api_key: str = None):
        super().__init__("Unsplash")
        self.api_key = api_key or os.environ.get('UNSPLASH_KEY', '')

    def fetch_image(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        if not self.api_key:
            return None
        try:
            encoded_query = urllib.parse.quote(query)
            url = (
                f"https://api.unsplash.com/search/photos"
                f"?query={encoded_query}&per_page=1&orientation=landscape"
            )
            req = urllib.request.Request(url, headers={
                'Authorization': f'Client-ID {self.api_key}',
                'Accept-Version': 'v1',
            })
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
                results = data.get('results', [])
                if results:
                    photo = results[0]
                    return {
                        'url': photo['urls'].get('regular', photo['urls']['full']),
                        'thumbnail': photo['urls'].get('small', ''),
                        'provider': self.name,
                        'attribution': f"Photo by {photo['user']['name']} on Unsplash",
                        'license': photo['links'].get('html', ''),
                    }
        except Exception as e:
            logger.warning(f"Unsplash failed for {query}: {e}")
        return None


class PexelsProvider(ImageProvider):
    def __init__(self, api_key: str = None):
        super().__init__("Pexels")
        self.api_key = api_key or os.environ.get('PEXELS_KEY', '')

    def fetch_image(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        if not self.api_key:
            return None
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page=1&orientation=landscape"
            req = urllib.request.Request(url, headers={
                'Authorization': self.api_key,
            })
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
                photos = data.get('photos', [])
                if photos:
                    photo = photos[0]
                    return {
                        'url': photo['src'].get('landscape', photo['src']['original']),
                        'thumbnail': photo['src'].get('medium', ''),
                        'provider': self.name,
                        'attribution': f"Photo by {photo.get('photographer', 'Unknown')} on Pexels",
                        'license': photo.get('url', ''),
                    }
        except Exception as e:
            logger.warning(f"Pexels failed for {query}: {e}")
        return None


class WikimediaProvider(ImageProvider):
    """Fetch images from Wikipedia/Wikimedia Commons with landmark-specific queries."""
    _last_request_time = 0
    _min_interval = 0.5  # Rate limit: max 2 requests per second

    def __init__(self):
        super().__init__("Wikimedia", timeout=4)

    def fetch_image(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        # Rate limiting
        now = time.time()
        elapsed = now - WikimediaProvider._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        WikimediaProvider._last_request_time = time.time()

        try:
            # Try to find a Wikipedia article with a good image
            # Use only the core place name for better matches
            search_term = query.split(' India')[0].strip() if ' India' in query else query
            # Take first 2-3 meaningful words
            words = search_term.split()[:4]
            clean_query = ' '.join(words)

            encoded_query = urllib.parse.quote(clean_query)
            url = (
                f"https://en.wikipedia.org/w/api.php"
                f"?action=query&titles={encoded_query}"
                f"&prop=pageimages&format=json&pithumbsize=1200"
            )
            req = urllib.request.Request(url, headers={'User-Agent': 'TripMindAI/2.0 (travel planner app)'})
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
                pages = data.get('query', {}).get('pages', {})
                for page_id, page_data in pages.items():
                    if page_id == '-1':
                        continue
                    if 'thumbnail' in page_data:
                        return {
                            'url': page_data['thumbnail']['source'],
                            'thumbnail': page_data['thumbnail']['source'],
                            'provider': self.name,
                            'attribution': 'Wikimedia Commons',
                            'license': 'Creative Commons',
                        }
        except Exception as e:
            logger.warning(f"Wikimedia failed for {query}: {e}")
        return None


class PollinationsFallbackProvider(ImageProvider):
    """AI-generated images using Pollinations. Builds context-aware prompts."""

    def __init__(self):
        super().__init__("Pollinations")

    def fetch_image(self, query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
        # Build a detailed, context-aware prompt for high-quality AI images
        destination = context.get('canonical_location', '') if context else ''
        category = context.get('category', 'general') if context else 'general'

        # Build prompt with destination specifics
        if destination and destination.lower() != query.lower():
            prompt = (
                f"Ultra realistic cinematic travel photograph of {query} in {destination} India, "
                f"golden hour lighting, professional DSLR, National Geographic style, "
                f"vibrant colors, detailed, 8k quality"
            )
        else:
            prompt = (
                f"Ultra realistic cinematic travel photograph of {query}, "
                f"golden hour lighting, professional DSLR, National Geographic style, "
                f"vibrant colors, detailed, 8k quality"
            )

        encoded = urllib.parse.quote(prompt)
        return {
            'url': f"https://image.pollinations.ai/prompt/{encoded}?width=1200&height=800&nologo=true",
            'thumbnail': f"https://image.pollinations.ai/prompt/{encoded}?width=400&height=300&nologo=true",
            'provider': self.name,
            'attribution': 'AI Generated (Pollinations)',
            'license': 'Public Domain',
        }


class ImageEngine:
    """
    Manages the waterfall of image providers with circuit breakers.
    """
    def __init__(self, keys: Dict[str, str] = None):
        keys = keys or {}
        self.providers = [
            UnsplashProvider(keys.get("UNSPLASH_KEY")),
            PexelsProvider(keys.get("PEXELS_KEY")),
            WikimediaProvider(),
            PollinationsFallbackProvider(),
        ]

    def get_image(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Get the best available image for a query, trying providers in order."""
        for provider in self.providers:
            try:
                result = provider.fetch_image(query, context)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Provider {provider.name} error: {e}")
                continue

        # Ultimate fallback — context-aware Pollinations
        fallback = PollinationsFallbackProvider()
        return fallback.fetch_image(query, context)

    def get_hero_image(self, destination: str, category: str = 'general') -> Dict[str, str]:
        """Get a high-quality hero image for a destination using landmark-specific queries."""
        query = get_landmark_query(destination, category)
        context = {
            'canonical_location': destination,
            'category': category,
        }
        return self.get_image(query, context)

    def get_gallery_images(self, destination: str, category: str = 'general', limit: int = 5) -> List[Dict[str, str]]:
        """Get multiple gallery images for a destination."""
        queries = get_gallery_queries(destination, category)[:limit]
        images = []
        context = {
            'canonical_location': destination,
            'category': category,
        }
        for q in queries:
            img = self.get_image(q, context)
            if img:
                images.append(img)
        return images
