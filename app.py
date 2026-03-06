from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


SIMULATED_DATASETS = {
    "gender": {
        "labels": ["Group A (Majority)", "Group B (Minority)"],
        "approval_rates": [85, 42],
        "grouping": "Gender",
    },
    "age": {
        "labels": ["Age 26+ (Majority)", "Age 18-25 (Minority)"],
        "approval_rates": [78, 51],
        "grouping": "Age",
    },
}


def evaluate_fairness(payload: dict) -> dict:
    labels = payload.get("labels", ["Group A (Majority)", "Group B (Minority)"])
    approval_rates = payload.get("approval_rates", [85, 42])
    threshold = float(payload.get("threshold", 0.8))

    majority_rate = float(approval_rates[0])
    minority_rate = float(approval_rates[1])

    ratio = (minority_rate / majority_rate) if majority_rate else 0.0
    parity_gap = majority_rate - minority_rate
    status = "Bias Detected" if ratio < threshold else "Fair Model"

    recommendation = (
        "Review training data and feature engineering for proxy bias, then retrain with fairness constraints."
        if status == "Bias Detected"
        else "Continue monitoring with fresh cohorts and drift checks to sustain fairness over time."
    )

    return {
        "data": {
            "labels": labels,
            "approval_rates": approval_rates,
            "threshold": threshold,
            "required_minority_rate": round(majority_rate * threshold, 2),
        },
        "ratio": round(ratio, 2),
        "parity_gap": round(parity_gap, 2),
        "majority_rate": round(majority_rate, 2),
        "minority_rate": round(minority_rate, 2),
        "fairness_score": round(min(ratio / threshold, 1.0) * 100, 2) if threshold > 0 else 0,
        "status": status,
        "recommendation": recommendation,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/audit-data", methods=["GET", "POST"])
def audit_data():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        if not payload.get("approval_rates") or len(payload["approval_rates"]) != 2:
            return jsonify({"error": "approval_rates must contain exactly two numeric values."}), 400
        try:
            payload["approval_rates"] = [float(payload["approval_rates"][0]), float(payload["approval_rates"][1])]
            payload["threshold"] = float(payload.get("threshold", 0.8))
        except (TypeError, ValueError):
            return jsonify({"error": "approval_rates and threshold must be numeric."}), 400

        if payload["approval_rates"][0] <= 0 or payload["approval_rates"][1] < 0:
            return jsonify({"error": "approval_rates must be valid percentages and majority must be > 0."}), 400

        if payload["approval_rates"][0] > 100 or payload["approval_rates"][1] > 100:
            return jsonify({"error": "approval_rates must be in the range 0-100."}), 400

        if payload["threshold"] <= 0 or payload["threshold"] > 1:
            return jsonify({"error": "threshold must be in the range (0, 1]."}), 400

        return jsonify(evaluate_fairness(payload))

    dimension = request.args.get("dimension", "gender").lower()
    selected = SIMULATED_DATASETS.get(dimension, SIMULATED_DATASETS["gender"])
    payload = {
        "labels": selected["labels"],
        "approval_rates": selected["approval_rates"],
        "threshold": 0.8,
    }

    result = evaluate_fairness(payload)
    result["dimension"] = dimension
    result["grouping"] = selected["grouping"]
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)