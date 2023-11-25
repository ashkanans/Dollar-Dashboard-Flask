# Dollar-Dashboard-Flask
A Flask-based web application for monitoring and visualizing real-time and historical data related to the Dollar, featuring interactive tables and dynamic charts using Chart.js and DataTables.

# Project Dependencies

## Scraper

Install the packages required for web scraping:

```bash
pip install requests beautifulsoup4
```

## Flask Web App

Install Flask:

```bash
pip install Flask
```

## HTML File Dependencies

The HTML file includes external dependencies such as Chart.js, Bootstrap, and DataTables. These are included through CDN links in the HTML file, so no separate installation is required. Ensure your internet connection is active when running the Flask app to fetch these dependencies.

# Running the Project

Once dependencies are installed, navigate to the project directory and run your Flask application:

```bash
python web_app.py
```

Access the app in your web browser at http://127.0.0.1:5000/.
