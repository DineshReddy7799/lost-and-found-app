🔎 Lost & Found Application

The Lost & Found Application is a feature-rich, community-focused system designed to demonstrate a high-fidelity, scalable solution for item recovery within a defined area (such as a campus or corporate environment).

This project is built as a Frontend-First Prototype, showcasing a fully interactive user experience powered primarily by client-side logic.

✨ Key Features
🔍 Geospatial Search

Supports Search Along the Route functionality.

Users can locate reported items within a specific radius or path drawn on the map.

🗺️ Smart Location Mapping

Map integration powered by Leaflet.js.

Users can input locations via:

Geocoding (typing an address/place).

Direct map interaction (click-to-select).

Complex coordinates are abstracted for a seamless UX.

🤖 Intelligent Matching

A client-side Smart Matching Algorithm detects high-probability connections between Lost and Found reports using:

Keyword similarity

Geographical proximity

📂 Comprehensive Listings

Category and type filters

Visual browsing of all active reports

Fast, powerful search interface

💬 Mock Communication

In-app simulated messaging between item owners and finders.

🎨 Modern UX

Clean, responsive UI inspired by a professional Figma design.

💻 Technical Stack & Architecture
Category	Technology	Purpose
Backend Serving	Django (Python)	Lightweight server for templates & static files during prototype stage.
Frontend Logic	Vanilla JavaScript	Handles business logic, dynamic rendering & app state.
Geospatial	Leaflet.js	Map rendering and client-side geospatial calculations.
Geocoding API	OpenStreetMap Nominatim	Converts addresses and place names to Lat/Lon coordinates.
Styling	HTML5 / CSS3 (Bootstrap 5)	Responsive design and UI components.
🏗 Architectural Note

This project adopts a Frontend-First/Decoupled Architecture.
All major logic currently runs on the client side.

The codebase is prepared for future integration with Supabase (Postgres, Auth, Real-time APIs, Storage) to transform it into a full-scale production-ready application.

⚙️ Setup & Installation

Follow the steps below to run the application locally.

1️⃣ Prerequisites

Ensure Python is installed.

2️⃣ Environment Setup

Navigate to your project directory (Lost_and_Found) and run:

# Create a virtual environment
python -m venv env

# Activate the virtual environment (Windows PowerShell)
.\env\Scripts\activate

# OR (macOS/Linux)
# source env/bin/activate

3️⃣ Install Dependencies
pip install django

4️⃣ Run the Application
python manage.py runserver

5️⃣ Access the App

Open your browser and visit:

Main App Dashboard:
http://127.0.0.1:8000/app/

Static Landing Page:
http://127.0.0.1:8000/
