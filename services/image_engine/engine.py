import hashlib
import logging
from typing import Dict, List, Optional
from core.models import DestinationImageCache
from .providers import ImageEngine, get_landmark_query, get_gallery_queries

logger = logging.getLogger(__name__)


class ImageRetrievalService:
    """High-level service for fetching contextual images with caching."""

    def __init__(self):
        self.engine = ImageEngine()

    def _get_query_hash(self, query: str) -> str:
        return hashlib.sha256(query.encode('utf-8')).hexdigest()

    def get_image(self, visual_meta: dict) -> dict:
        """
        Retrieves the best image for the given visual metadata.
        Returns a dict with url, thumbnail, and attribution.
        """
        if not visual_meta:
            return self._fallback_image("travel destination")

        primary_query = visual_meta.get('primary_query')
        if not primary_query:
            return self._fallback_image("travel destination")

        query_hash = self._get_query_hash(primary_query)

        # 1. Check Cache
        cached = DestinationImageCache.objects.filter(query_hash=query_hash).first()
        if cached:
            return {
                "url": cached.image_url,
                "thumbnail": cached.thumbnail_url or cached.image_url,
                "attribution_text": cached.attribution_text,
                "attribution_url": cached.attribution_url,
            }

        # 2. Retrieve from Providers
        destination = visual_meta.get("destination", visual_meta.get("city", ""))
        context = {
            "canonical_location": destination,
            "category": visual_meta.get("category", "general"),
        }
        best_image = self.engine.get_image(primary_query, context=context)

        # 3. Save to Cache
        if best_image and best_image.get('provider') != "LoremPicsum":
            try:
                DestinationImageCache.objects.create(
                    query_hash=query_hash,
                    query=primary_query[:500],
                    provider=best_image.get('provider', 'Unknown'),
                    image_url=best_image['url'],
                    thumbnail_url=best_image.get('thumbnail', best_image['url']),
                    attribution_text=best_image.get('attribution', ''),
                    attribution_url=best_image.get('license', ''),
                )
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")

        return best_image

    def get_hero_image(self, destination: str, category: str = 'general') -> dict:
        """Get a context-aware hero image for a destination."""
        query = get_landmark_query(destination, category)
        query_hash = self._get_query_hash(f"hero_{query}")

        # Check cache
        cached = DestinationImageCache.objects.filter(query_hash=query_hash).first()
        if cached:
            return {
                "url": cached.image_url,
                "thumbnail": cached.thumbnail_url or cached.image_url,
                "attribution_text": cached.attribution_text,
                "attribution_url": cached.attribution_url,
                "provider": cached.provider,
            }

        # Fetch new
        result = self.engine.get_hero_image(destination, category)

        # Cache
        if result and result.get('provider') != "LoremPicsum":
            try:
                DestinationImageCache.objects.create(
                    query_hash=query_hash,
                    query=f"hero: {query}"[:500],
                    provider=result.get('provider', 'Unknown'),
                    image_url=result['url'],
                    thumbnail_url=result.get('thumbnail', result['url']),
                    attribution_text=result.get('attribution', ''),
                    attribution_url=result.get('license', ''),
                )
            except Exception as e:
                logger.warning(f"Hero cache write failed: {e}")

        return result

    def get_gallery_images(self, destination: str, category: str = 'general', limit: int = 5) -> list:
        """Get multiple gallery images for a destination."""
        queries = get_gallery_queries(destination, category)[:limit]
        images = []

        for q in queries:
            query_hash = self._get_query_hash(f"gallery_{q}")

            # Check cache first
            cached = DestinationImageCache.objects.filter(query_hash=query_hash).first()
            if cached:
                images.append({
                    "url": cached.image_url,
                    "thumbnail": cached.thumbnail_url or cached.image_url,
                    "attribution_text": cached.attribution_text,
                    "attribution_url": cached.attribution_url,
                    "provider": cached.provider,
                    "query": q,
                })
                continue

            # Fetch new
            context = {"canonical_location": destination, "category": category}
            result = self.engine.get_image(q, context=context)
            if result:
                result['query'] = q
                images.append(result)

                # Cache
                if result.get('provider') != "LoremPicsum":
                    try:
                        DestinationImageCache.objects.create(
                            query_hash=query_hash,
                            query=f"gallery: {q}"[:500],
                            provider=result.get('provider', 'Unknown'),
                            image_url=result['url'],
                            thumbnail_url=result.get('thumbnail', result['url']),
                            attribution_text=result.get('attribution', ''),
                            attribution_url=result.get('license', ''),
                        )
                    except Exception as e:
                        logger.warning(f"Gallery cache write failed: {e}")

        return images

    def _fallback_image(self, query: str) -> dict:
        context = {"canonical_location": "", "category": "general"}
        return self.engine.get_image(query, context=context)
