<div align="center">
  <img src="https://placehold.co/120x120/f59e0b/ffffff?text=TM" alt="TripMind AI Logo" width="120" height="120">
  
  # TripMind AI ✈️
  
  **Your Premium AI-Powered Travel Architect**
  
  [![Status: Ongoing](https://img.shields.io/badge/Status-Ongoing_Project-f59e0b?style=for-the-badge&logo=github)](https://github.com/HiteshKPatel674/TRIPMIND-AI)
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
  
  <p align="center">
    TripMind AI creates stunning, personalized itineraries in seconds. Complete with integrated flight, hotel, and attraction recommendations in a cinematic user interface.
  </p>
</div>

---

> ⚠️ **Note:** TripMind AI is currently an **ongoing project**. Features are actively being developed, and the architecture is evolving. Expect frequent updates!

## ✨ Features

- **🤖 AI-Crafted Itineraries**: Generates day-by-day smart itineraries based on your budget, travel style, and preferences.
- **📸 Intelligent Image Engine**: A sophisticated multi-provider waterfall system (Unsplash -> Pexels -> Wikimedia -> Pollinations.ai) to source high-quality, landmark-specific imagery.
- **🏨 Smart Booking Integration**: Real-time integration with Google Hotels (via SerpApi) for live pricing and booking links.
- **🧠 Destination Knowledge Hub**: Aggregates essential travel facts, cultural tips, language, and transport information on the fly.
- **✨ Cinematic User Interface**: A premium glassmorphic frontend inspired by Apple Maps and Airbnb, featuring smooth transitions and interactive day panels.
- **🗺️ Interactive Maps**: Built-in Leaflet maps to visualize your journey.

## 🛠️ Tech Stack

- **Backend**: Python, Django
- **Frontend**: HTML5, Vanilla JS, CSS3 (Custom Premium Design System)
- **Database**: SQLite (Development)
- **AI / APIs**: OpenAI/Anthropic (via LangChain), SerpApi (Hotels/Flights), OpenStreetMap/Nominatim, Wikimedia

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- An API key for SerpApi (if fetching live hotels)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HiteshKPatel674/TRIPMIND-AI.git
   cd TRIPMIND-AI
   ```

2. **Set up a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   SERPAPI_KEY=your_serpapi_key
   ```

5. **Run Migrations & Start Server:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

6. **Open your browser:**
   Navigate to `http://localhost:8000` to start planning your trip!

## 🛣️ Roadmap

- [x] Integrate multi-provider image engine
- [x] Implement AI-driven knowledge hub
- [x] Live hotel pricing and mock transport
- [x] V4 Premium cinematic redesign
- [ ] Multi-user collaboration on itineraries
- [ ] Live flight API integration
- [ ] Export to Calendar (.ics) feature
- [ ] Mobile app (React Native)

## 🤝 Contributing

Since this is an ongoing project, contributions, issues, and feature requests are highly welcome! Feel free to check the [issues page](https://github.com/HiteshKPatel674/TRIPMIND-AI/issues).

---
<div align="center">
  <i>Built with ❤️ by Hitesh Patel</i>
</div>
