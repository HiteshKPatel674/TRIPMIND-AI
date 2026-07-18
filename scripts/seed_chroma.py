#!/usr/bin/env python
"""
seed_chroma.py — Populate ChromaDB with curated Indian travel documents.

Run from the project root:
    python tripmind/scripts/seed_chroma.py
"""

import os
import sys

# ── Django bootstrap ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tripmind.settings")

import django  # noqa: E402
django.setup()

from agent.rag import add_travel_doc  # noqa: E402

# ── Travel Knowledge Base ─────────────────────────────────────────────────────

DOCS = [
    {
        "id": "goa-beach",
        "destination": "Goa",
        "category": "beach",
        "text": (
            "Goa's best beaches include Baga Beach, Calangute Beach, and the quieter "
            "Palolem Beach in South Goa. Water sports at Baga range from parasailing "
            "(₹500–800) to jet skiing (₹1,000–2,000) and banana boat rides (₹300). "
            "Beach shacks like Britto's and Curlies serve fresh seafood meals for "
            "₹300–800 per person. The Anjuna Flea Market every Wednesday is a must for "
            "souvenirs, hippie clothes, and local jewellery. The best season to visit "
            "Goa's beaches is November to February when the weather is dry, sunny, and "
            "temperatures hover around 25–32°C. Avoid the monsoon months (June–September) "
            "if you want beach activities, as most shacks close and the sea is rough."
        ),
    },
    {
        "id": "goa-food",
        "destination": "Goa",
        "category": "food",
        "text": (
            "Goa is a food lover's paradise blending Portuguese and Konkani cuisines. "
            "The legendary fish thali at Ritz Classic in Panjim costs just ₹200 and "
            "includes fried fish, rice, dal, and sol kadhi. Try the fiery pork Vindaloo "
            "at Fernando's Nostalgia in Rua de Ourem — a plate costs around ₹350. "
            "Bebinca, the traditional Goan layered dessert, is available at local "
            "bakeries in Fontainhas (₹80–150 per piece). The Fontainhas Latin Quarter "
            "in Panjim is perfect for a heritage food walk — narrow colourful streets "
            "lined with cafés serving authentic Goan poi bread and chorizo pao (₹60–100). "
            "For seafood, visit Martin's Corner in Betalbatim for butter garlic prawns "
            "(₹600) and Goan sausage chilly fry (₹280)."
        ),
    },
    {
        "id": "goa-general",
        "destination": "Goa",
        "category": "general",
        "text": (
            "Beyond beaches, Goa offers rich history and nature. Old Goa's churches, "
            "including the UNESCO-listed Basilica of Bom Jesus (free entry) and Se "
            "Cathedral, showcase stunning Portuguese-era architecture. Fort Aguada, "
            "built in 1612, offers panoramic views of the Arabian Sea (entry ₹25). "
            "Dudhsagar Falls, one of India's tallest waterfalls, is accessible via a "
            "thrilling jeep ride from Mollem (₹600 per person, 45 minutes each way). "
            "Rent a scooter for ₹300/day to explore at your own pace — it's the most "
            "popular way to get around. Spice plantations in Ponda offer guided tours "
            "with lunch for ₹400–600. A Mandovi River cruise in the evening costs ₹200 "
            "and includes live music and Goan folk dances."
        ),
    },
    {
        "id": "kerala-backwaters",
        "destination": "Kerala",
        "category": "general",
        "text": (
            "The Kerala backwaters are best experienced from Alleppey (Alappuzha), "
            "where you can hire a traditional kettuvallam houseboat for ₹6,000–12,000 "
            "per night depending on the season and amenities. The houseboat cruise "
            "through palm-fringed canals includes freshly cooked Kerala meals — fish "
            "curry, appam, and coconut-based dishes. Kumarakom Bird Sanctuary on "
            "Vembanad Lake is a haven for birdwatchers (entry ₹50, boat ride ₹150). "
            "From Alleppey, take a day trip to Munnar (4 hours), known for its rolling "
            "tea gardens, Eravikulam National Park (₹125 entry, home to Nilgiri Tahr), "
            "and the Mattupetty Dam. Best time to visit is September to March. "
            "Kerala is also famous for Ayurvedic spa treatments starting at ₹1,500 "
            "for a full-body Abhyanga massage."
        ),
    },
    {
        "id": "kerala-general",
        "destination": "Kerala",
        "category": "general",
        "text": (
            "Kerala, 'God's Own Country', offers diverse experiences beyond backwaters. "
            "Kovalam Beach near Trivandrum has a picturesque lighthouse and calm waters "
            "ideal for swimming. Periyar Wildlife Sanctuary in Thekkady offers bamboo "
            "rafting (₹300) and guided jungle treks to spot elephants and sambar deer. "
            "Watch a Kathakali performance in Kochi (₹300 with makeup session viewing). "
            "Fort Kochi's heritage area has the famous Chinese fishing nets, St. Francis "
            "Church (India's oldest European church), and Jew Town's antique shops. "
            "Local transport tip: Kerala's state buses are cheap (₹15–50) but hire an "
            "auto-rickshaw for short trips (₹30–100). Must-try food: Kerala sadhya "
            "(vegetarian feast on banana leaf, ₹150–250) and Malabar biryani (₹120–200)."
        ),
    },
    {
        "id": "manali-adventure",
        "destination": "Manali",
        "category": "adventure",
        "text": (
            "Manali is the adventure capital of Himachal Pradesh. Solang Valley, just "
            "14 km from Manali, offers paragliding (₹2,500 for a 15-minute tandem "
            "flight), zorbing (₹500), and skiing in winter (₹1,000/hour with gear). "
            "Rohtang Pass at 3,978 m requires a permit (₹500, book online at "
            "rohtangpermits.hp.gov.in) and is open only May to November. White-water "
            "rafting on the Beas River starts from Pirdi — a 14 km stretch costs "
            "₹1,000–1,500 and takes 1.5 hours with Grade II–III rapids. Old Manali is "
            "a backpacker hub with cafés like Lazy Dog and Drifter's Café serving wood-fired "
            "pizza (₹300) and Israeli food. For trekking, the Jogini Falls trail from "
            "Vashisht village is an easy 2-hour hike with stunning valley views."
        ),
    },
    {
        "id": "manali-general",
        "destination": "Manali",
        "category": "general",
        "text": (
            "Manali offers natural beauty and culture year-round. The Hadimba Temple, "
            "a 1553 wooden shrine set in a cedar forest, has free entry and is one of "
            "Manali's most iconic landmarks. The Jogini Falls trek starts from Vashisht "
            "and takes about 2 hours through apple orchards. Mall Road is the main "
            "shopping street — pick up Kullu shawls (₹500–3,000), Himachali caps (₹200), "
            "and dried fruits. The best time to visit is May–June for pleasant weather "
            "(15–25°C) and December–February for snowfall and winter sports. Budget "
            "hotels start at ₹800/night while mid-range options are ₹2,000–4,000. "
            "HRTC Volvo buses from Delhi to Manali cost ₹1,000–1,500 (12 hours). "
            "Local tip: visit Naggar Castle (₹15 entry) for art galleries and Roerich Museum."
        ),
    },
    {
        "id": "rajasthan-jaipur",
        "destination": "Jaipur",
        "category": "general",
        "text": (
            "Jaipur, the Pink City, is Rajasthan's crown jewel. Amber Fort (₹500 for "
            "foreigners, ₹100 for Indians) features stunning Sheesh Mahal mirror work "
            "and an elephant ride option (₹1,100). Hawa Mahal, the iconic Palace of "
            "Winds, costs just ₹50 entry and is best photographed from the street-side "
            "café opposite. City Palace (₹500) houses a museum with royal artefacts "
            "and the world's largest silver vessels. Drive up to Nahargarh Fort in the "
            "evening for a breathtaking sunset over the city — the Padao restaurant "
            "there serves thalis for ₹250. Johri Bazaar is famous for Jaipur's traditional "
            "Kundan and Meenakari jewellery, and Rajasthani jutti shoes (₹300–800). "
            "Best season is October to March; summers exceed 45°C."
        ),
    },
    {
        "id": "rajasthan-udaipur",
        "destination": "Udaipur",
        "category": "general",
        "text": (
            "Udaipur, the City of Lakes, is India's most romantic destination. A boat "
            "ride on Lake Pichola (₹400 for an hour, ₹800 sunset cruise) passes the "
            "stunning Jag Mandir and Lake Palace. City Palace (₹300) is Rajasthan's "
            "largest palace complex with panoramic lake views from the terrace. Fateh "
            "Sagar Lake is ideal for an evening walk — pedal boats are ₹150/person. "
            "Saheliyon ki Bari (₹10 entry) is a beautiful garden with fountains, built "
            "for royal ladies. For dining, Ambrai Restaurant on the lakefront offers "
            "Rajasthani thali (₹350) with palace views. Budget hotels near Lal Ghat "
            "start at ₹600/night; heritage havelis range ₹3,000–8,000. Best time to "
            "visit is September to March. The Vintage Car Museum (₹250) houses rare "
            "Rolls Royces owned by the Mewar royal family."
        ),
    },
    {
        "id": "andaman-general",
        "destination": "Andaman",
        "category": "beach",
        "text": (
            "The Andaman Islands offer pristine beaches and world-class diving. "
            "Radhanagar Beach on Havelock Island is rated among Asia's best beaches "
            "— white sand, turquoise water, and spectacular sunsets. Cellular Jail in "
            "Port Blair is a must-visit (₹30 entry); the evening light-and-sound show "
            "(₹100) recounts India's freedom struggle. Scuba diving at Havelock costs "
            "₹3,500 for a discover dive (no experience needed) — expect to see "
            "clownfish, sea turtles, and coral gardens. Government ferries from Port "
            "Blair to Havelock cost ₹1,200 (2.5 hours); private Makruzz ferries are "
            "₹1,800 but faster (90 minutes). Snorkelling at Elephant Beach is ₹600 "
            "including gear. Best time is November to April; monsoons shut down most "
            "water activities. Budget stays on Havelock start at ₹1,500/night."
        ),
    },
    {
        "id": "ladakh-general",
        "destination": "Ladakh",
        "category": "adventure",
        "text": (
            "Ladakh is India's ultimate high-altitude adventure destination. Pangong "
            "Lake (4,350 m) is a surreal blue lake on the India-China border — "
            "overnight camping costs ₹2,000–4,000 per tent. Nubra Valley, accessed "
            "via Khardung La (one of the world's highest motorable passes at 5,359 m), "
            "features sand dunes and double-humped Bactrian camels (₹300 ride). "
            "Leh Palace, modelled after the Potala Palace, offers ₹30 entry and "
            "panoramic city views. The best time to visit is June to September when "
            "roads are open and skies are clear. Critical tip: acclimatize for at "
            "least 2 days in Leh before heading to higher altitudes to avoid altitude "
            "sickness. Inner Line Permits are needed for Pangong and Nubra (₹400, "
            "obtainable in Leh). Bike rentals (Royal Enfield) cost ₹1,200–1,800/day."
        ),
    },
    {
        "id": "coorg-general",
        "destination": "Coorg",
        "category": "general",
        "text": (
            "Coorg (Kodagu) in Karnataka is a lush hill station known as the 'Scotland "
            "of India'. Abbey Falls, surrounded by coffee plantations and spice estates, "
            "is a scenic 15-minute walk from the parking (₹15 entry). Raja's Seat "
            "garden in Madikeri offers sunset views with a musical fountain show in the "
            "evening (₹10). Dubare Elephant Camp on the Kaveri River lets you bathe and "
            "feed elephants (₹200, morning hours only). Coffee plantation stays are "
            "Coorg's highlight — homestays range from ₹2,000–4,000/night including "
            "home-cooked Kodava cuisine (pork curry, akki rotti, and bamboo shoot "
            "curry). Talacauvery, the birthplace of the River Kaveri, is a sacred site "
            "worth visiting. Best time is October to March; monsoon season (June–Sept) "
            "brings heavy rain but stunning green landscapes."
        ),
    },
    {
        "id": "mysore-general",
        "destination": "Mysore",
        "category": "general",
        "text": (
            "Mysore (Mysuru) is Karnataka's cultural capital, famous for its royal "
            "heritage. Mysore Palace, illuminated by 97,000 bulbs on Sundays and "
            "public holidays, is India's most visited monument (₹70 entry). Chamundi "
            "Hills, topped by the Chamundeshwari Temple, offers panoramic city views — "
            "climb the 1,008 steps or drive up. Brindavan Gardens at KRS Dam feature "
            "musical fountains in the evening (₹15 entry, ₹75 for the fountain show). "
            "Devaraja Market is a 130-year-old bazaar selling flowers, spices, incense, "
            "and Mysore sandalwood products. Don't miss Mysore Pak, the iconic sweet "
            "invented at the royal kitchen — buy from Guru Sweets (₹400/kg). Mysore "
            "silk sarees from KSIC showroom start at ₹3,000. Best time to visit is "
            "Dussehra season (October) for the grand royal procession."
        ),
    },
    {
        "id": "ooty-general",
        "destination": "Ooty",
        "category": "general",
        "text": (
            "Ooty (Udhagamandalam) in Tamil Nadu's Nilgiri Hills is a classic Indian "
            "hill station. The Government Botanical Gardens, established in 1848, house "
            "rare plant species and a fossilized tree trunk (₹30 entry). The Nilgiri "
            "Mountain Railway, a UNESCO World Heritage toy train from Mettupalayam to "
            "Ooty, costs ₹300 for first class (5 hours, book early on IRCTC). Ooty "
            "Lake offers paddle and row boating (₹200/30 minutes). Doddabetta Peak "
            "(2,637 m) is the highest point in the Nilgiris — a telescope house at the "
            "top costs ₹10. Try Ooty's famous homemade chocolates from King Star or "
            "Moddy's (₹300–500/kg). Budget hotels start at ₹1,000/night; colonial-era "
            "properties like Savoy Hotel cost ₹5,000+. Best time is April to June; "
            "winter (Nov–Feb) is cold (5–15°C) but less crowded."
        ),
    },
    {
        "id": "rishikesh-general",
        "destination": "Rishikesh",
        "category": "adventure",
        "text": (
            "Rishikesh, the Yoga Capital of the World, sits on the banks of the Ganges "
            "in Uttarakhand. Ram Jhula and Laxman Jhula are iconic suspension bridges "
            "with temples and ashrams on both banks. White-water rafting is the top "
            "activity — 16 km stretches from Shivpuri to Rishikesh cost ₹600–1,500 "
            "depending on the season, covering Grade III–IV rapids like Roller Coaster "
            "and Golf Course. The Beatles Ashram (Chaurasi Kutia) where the band "
            "stayed in 1968 costs ₹600 entry and features street art and meditation "
            "halls. Yoga retreats and classes are available everywhere — drop-in classes "
            "at Parmarth Niketan or Sivananda Ashram cost ₹500/class. Bungee jumping "
            "from Jumpin Heights (83 m) costs ₹3,550. Ganga Aarti at Triveni Ghat "
            "every evening is free and deeply spiritual. Best time is February to May "
            "and September to November."
        ),
    },
]


def main():
    print("=" * 60)
    print("  TripMind AI — Seeding ChromaDB with travel knowledge")
    print("=" * 60)
    print()

    total = len(DOCS)
    for idx, doc in enumerate(DOCS, start=1):
        print(f"  [{idx:2d}/{total}] Adding: {doc['id']:25s} ({doc['destination']}, {doc['category']})")
        add_travel_doc(
            doc_id=doc["id"],
            text=doc["text"],
            destination=doc["destination"],
            category=doc["category"],
        )

    print()
    print(f"  ✅ Successfully seeded {total} documents into ChromaDB.")
    print("=" * 60)


if __name__ == "__main__":
    main()
