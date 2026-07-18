<div align="center">

# TripMind AI

### AI-Powered Intelligent Travel Itinerary Planning Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=flat-square&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](https://developer.mozilla.org/)
[![Status](https://img.shields.io/badge/Status-Active%20Development-success?style=flat-square)]()

An AI-powered travel planning platform that automatically generates personalized travel itineraries using Large Language Models (LLMs), destination intelligence, real-time hotel recommendations, and interactive maps.

</div>

---

# Overview

TripMind AI is a full-stack web application that simplifies travel planning by combining generative AI with real-time travel information.

Instead of manually searching across multiple websites, users provide trip preferences such as destination, budget, travel style, and duration. The platform generates a structured day-by-day itinerary enriched with destination insights, accommodation suggestions, transportation information, and landmark images.

The project focuses on building scalable AI workflows rather than simply integrating an LLM.

---

# Key Features

### AI-Powered Itinerary Generation

- Personalized trip plans
- Day-wise scheduling
- Budget-aware recommendations
- Travel preference optimization

---

### Destination Intelligence Engine

Automatically gathers:

- History
- Culture
- Language
- Currency
- Transportation
- Safety information
- Local travel tips

---

### Intelligent Image Pipeline

Multi-source image retrieval system with automatic fallback:

```
Unsplash
     ↓
Pexels
     ↓
Wikimedia Commons
     ↓
Pollinations AI
```

Ensures destination-specific, high-quality imagery even when one provider fails.

---

### Smart Hotel Recommendation Engine

- Live hotel recommendations
- Booking links
- Price comparison
- Location-aware suggestions

---

### Interactive Maps

Built using Leaflet and OpenStreetMap to visualize destinations and itinerary locations.

---

### Responsive User Interface

- Fully responsive design
- Dynamic itinerary timeline
- Interactive day cards
- Modern glassmorphism UI

---

# System Architecture

```
                        User
                          │
                          ▼
                 Frontend (HTML/CSS/JS)
                          │
                          ▼
                    Django Backend
                          │
      ┌───────────────────┼────────────────────┐
      ▼                   ▼                    ▼
 Destination API      Hotel Service      Image Engine
      │                   │                    │
      ▼                   ▼                    ▼
 Knowledge Hub      Booking Links      Multi-source Images
                          │
                          ▼
                    AI Processing
                          │
                          ▼
                Personalized Itinerary
```

---

# Technology Stack

## Backend

- Python
- Django
- Django Templates

## Frontend

- HTML5
- CSS3
- JavaScript (ES6)

## Database

- SQLite (Development)

## AI & External APIs

- LangChain
- OpenAI / Anthropic
- SerpAPI
- OpenStreetMap
- Nominatim
- Wikimedia Commons
- Pollinations AI

---

# Project Structure

```
TripMind-AI/

├── planner/
├── templates/
├── static/
├── media/
├── utils/
├── services/
├── itinerary/
├── requirements.txt
├── manage.py
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/HiteshKPatel674/TRIPMIND-AI.git
cd TRIPMIND-AI
```

## Create Virtual Environment

```bash
python -m venv venv
```

Windows

```bash
venv\Scripts\activate
```

Linux / macOS

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Configure Environment Variables

Create a `.env` file.

```env
SECRET_KEY=

SERPAPI_KEY=

OPENAI_API_KEY=
```

## Run

```bash
python manage.py migrate

python manage.py runserver
```

Open

```
http://127.0.0.1:8000
```

---

# Future Improvements

- Flight API integration
- User authentication
- Collaborative trip planning
- PDF itinerary export
- Calendar integration
- Payment gateway
- AI chat assistant
- Mobile application

---

# Screenshots

> Add screenshots here after completing the UI.

```
Home Page

Trip Planner

Generated Itinerary

Destination Details

Hotel Recommendations
```

---

# Engineering Highlights

- Designed modular backend architecture using Django
- Built an AI-assisted itinerary generation workflow
- Developed a multi-provider image retrieval pipeline with automatic fallback
- Integrated real-time hotel recommendation APIs
- Implemented scalable service-layer architecture
- Built reusable frontend components with responsive layouts

---

# Current Status

This project is under active development. Core itinerary generation, destination intelligence, hotel recommendations, and image retrieval are implemented, while additional features such as flight booking, authentication, and collaboration are currently in progress.

---

# Author

**Hitesh Patel**

AI/ML Engineer

LinkedIn: *(Add Link)*

Email: *(Add Email)*
