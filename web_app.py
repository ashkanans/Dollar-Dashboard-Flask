from flask import Flask, render_template, jsonify
import time
from Scraper import Scraper

app = Flask(__name__)

scraper = Scraper()
scraper.scrape()
scraper.load_from_database()


# Route to get updated data as JSON
@app.route('/updated')
def get_updated_data():
    scraper = Scraper()
    scraper.scrape()
    scraper.load_from_database()

    # Return updated data as JSON
    data = {
        'last_update': scraper.last_update,
        'data_dpag': scraper.data_dpag,
        'data_dp': scraper.data_dp,
        'data_dt': scraper.data_dt,
        'data_dpa': scraper.data_dpa
    }
    return jsonify(data)


# Define routes and corresponding functions
@app.route('/')
def index():
    return render_template('index.html',
                           scraper=scraper,
                           data_dpa=scraper.data_dpa,
                           data_dp=scraper.data_dp,
                           data_dt=scraper.data_dt,
                           data_dpag=scraper.data_dpag)


if __name__ == '__main__':
    # Run the Flask app in debug mode
    app.run(debug=True)
