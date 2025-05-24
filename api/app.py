from flask import Flask, request, jsonify
import pandas as pd
import pickle
import joblib

app = Flask(__name__)

# Load encoder and model
with open("../models/transformers/label_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

model = joblib.load("../models/model.pkl")

def encode_feature(encoder, value):
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    else:
        return -1


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    try:
        cat_cols = ['priority', 'category', 'issueType', 'severity']
        encoded = {
            col: encode_feature(encoders[col], data[col])
            for col in cat_cols
        }

    except Exception as e:
        return jsonify({"error": f"Encoding failed: {str(e)}"}), 400

    try:
        creation_date = pd.to_datetime(data["creationDate"])
        creation_month = creation_date.month
        creation_day_of_week = creation_date.dayofweek
        is_weekend = int(creation_day_of_week in [5, 6])
    except Exception as e:
        return jsonify({"error": f"Date parsing failed: {str(e)}"}), 400

    input_df = pd.DataFrame([{
        "priority": encoded["priority"],
        "category": encoded["category"],
        "issueType": encoded["issueType"],
        "creation_month": creation_month,
        "is_weekend": is_weekend,
        "creation_day_of_week": creation_day_of_week
    }])

    try:
        prediction = model.predict(input_df)[0]
        return jsonify({"estimated_resolution_time_hours": round(prediction, 2)})
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
