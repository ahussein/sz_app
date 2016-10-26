"""
WSGI engry point of the backend app
"""
from app import app

if __name__ == "__main__":
    app.app.run(debug=True, host='0.0.0.0' ,port=8080)