from flask import Flask, render_template
import requests

app = Flask(__name__)

# URL of the /health API
HEALTH_API_URL = "http://127.0.0.1:5001/health"

@app.route("/dashboard")
def dashboard():
    """Render the dashboard template with data from the /health API."""
    try:
        # Fetch data from the /health API
        response = requests.get(HEALTH_API_URL)
        if response.status_code == 200:
            health_data = response.json()
        else:
            health_data = {"error": "Unable to fetch health data"}
    except Exception as e:
        health_data = {"error": str(e)}

    return render_template("dashboard.html", health_data=health_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
