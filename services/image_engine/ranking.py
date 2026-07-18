def rank_images(images: list[dict], visual_meta: dict) -> list[dict]:
    """
    Ranks images based on relevance and quality.
    Each image is a dict from a provider.
    visual_meta contains type, city, country, landmark, etc.
    """
    for img in images:
        score = 0
        
        # 1. Image Resolution (higher is better, cap at +20)
        width = img.get('width', 0)
        height = img.get('height', 0)
        if width > 800 and height > 400:
            score += 10
        if width >= 1200:
            score += 10
            
        # 2. Landscape Orientation (+15)
        if width > height:
            score += 15
            
        # 3. Location Match in URL or Attribution (+25)
        city = visual_meta.get('city', '').lower()
        landmark = visual_meta.get('landmark', '').lower()
        
        attr_text = img.get('attribution_text', '').lower()
        img_url = img.get('url', '').lower()
        
        if landmark and (landmark in attr_text or landmark.replace(' ', '_') in img_url):
            score += 25
        elif city and (city in attr_text or city.replace(' ', '_') in img_url):
            score += 15
            
        img['score'] = score
        
    return sorted(images, key=lambda x: x.get('score', 0), reverse=True)
