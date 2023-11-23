from flask import Flask, render_template

from Scraper import Scraper

app = Flask(__name__)

scraper = Scraper()
scraper.scrape()


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
    app.run(debug=True)
