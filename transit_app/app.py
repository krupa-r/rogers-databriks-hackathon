import os
from flask import Flask, jsonify, request, send_from_directory
from databricks import sql
from databricks.sdk.core import Config

app = Flask(__name__, static_folder="static", static_url_path="")
cfg = Config()  # auto-authenticates as the app's own identity — no token to manage

def get_connection():
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
        credentials_provider=lambda: cfg.authenticate,
    )

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/predict")
def predict():
    date = request.args.get("date")
    hour = int(request.args.get("hour"))
    weather = request.args.get("weather")

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT predicted_device_count, recommended_frequency, scheduled_frequency
            FROM workspace.transit.gold_predictions
            WHERE event_date = %s AND hour(event_hour) = %s AND weather_condition = %s
            """,
            (date, hour, weather),
        )
        row = cur.fetchone()

    if not row:
        return jsonify({"error": "no prediction for this combination"}), 404
    return jsonify({
        "predictedDeviceCount": row[0],
        "recommendedFrequency": row[1],
        "scheduledFrequency": row[2],
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", 8000)))