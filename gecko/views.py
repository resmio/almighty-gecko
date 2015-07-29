from flask import Flask
from flask_geckoboard import Geckoboard

app = Flask(__name__)
geckoboard = Geckoboard(app)


@app.route('/test')
@geckoboard.number
def test():
    return (123, 1234)
