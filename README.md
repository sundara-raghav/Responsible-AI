# Responsible-AI

FairLoan AI is a lightweight Responsible AI dashboard that audits model outcomes for potential demographic bias.

## Features

- Simulated demographic audit datasets (`gender`, `age`)
- Disparate Impact Ratio calculation (`minority_rate / majority_rate`)
- 80% rule fairness check
- Additional metrics: parity gap and fairness score
- Custom simulation form for manual group labels, approval rates, and threshold
- Input validation for custom audit API requests
- KPI cards and recent audit history panel
- Dual Chart.js visuals: approval comparison + observed-vs-threshold ratio
- Interactive Chart.js visualization
- Actionable Responsible AI recommendation text
- Responsive dashboard layout for mobile and desktop

## Project Structure

- `app.py`: Flask server and fairness metric logic
- `templates/index.html`: Dashboard UI
- `static/app.js`: Frontend audit and chart logic
- `static/style.css`: Dashboard styling
- `requirements.txt`: Python dependencies

## Run Locally

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python app.py
```

4. Open `http://127.0.0.1:5000` in your browser.

## API

- `GET /audit-data?dimension=gender|age`
	- Returns simulated audit data, disparate impact ratio, status, and recommendation.

- `POST /audit-data`
	- Accepts custom JSON input:

```json
{
	"labels": ["Group A (Majority)", "Group B (Minority)"],
	"approval_rates": [85, 42],
	"threshold": 0.8
}
```

	- Returns computed fairness metrics for the provided dataset.