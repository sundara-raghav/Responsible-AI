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
- Purpose-bound data minimization with PII masking and audit logging
- GitHub Actions CI/CD workflow for test and Render deployment automation

## Project Structure

- `app.py`: Flask server and fairness metric logic
- `utils/data_minimizer.py`: Data minimization utility class
- `config/purpose_field_map.json`: Purpose-to-allowed-fields mapping
- `templates/index.html`: Dashboard UI
- `static/app.js`: Frontend audit and chart logic
- `static/style.css`: Dashboard styling
- `tests/test_data_minimizer.py`: Pytest suite for minimization utility and API
- `.github/workflows/ci-cd.yml`: CI/CD workflow for testing and deployment
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

- `POST /api/minimize`
	- Accepts minimization JSON input:

```json
{
	"purpose": "analytics",
	"data": [
		{
			"user_id": 1,
			"name": "Alice Johnson",
			"email": "alice@example.com",
			"phone": "+1-202-555-0134",
			"age": 24,
			"country": "US",
			"transaction_amount": 120.0,
			"is_fraud": 0
		}
	]
}
```

	- Returns minimized records and an audit log.

## Data Minimization Principle

Under GDPR Article 5(1)(c), personal data should be adequate, relevant, and limited to what is necessary for a specific purpose. This project implements that principle by enforcing purpose-based field selection and privacy-preserving transformations before data use.

### How It Is Implemented

- `DataMinimizer` in `utils/data_minimizer.py` drops fields not required for the selected purpose.
- PII masking is applied:
	- `email` is hashed with SHA-256.
	- `phone` is reduced to last 4 digits.
	- `name` becomes first letter plus `***`.
- Quasi-identifier suppression is applied:
	- `age` is converted to `age_group` buckets (`18-25`, `26-35`, etc.).
- Every minimization action is logged with timestamp, fields dropped, fields masked, and purpose.

### Configure Purpose Mapping

Purpose-specific fields are configured in `config/purpose_field_map.json`.

- Add or update a purpose key.
- List only the fields required for that purpose.
- Any field not in the list is automatically dropped.

### API Example with curl

```bash
curl -X POST http://127.0.0.1:5000/api/minimize \
	-H "Content-Type: application/json" \
	-d '{
		"purpose": "analytics",
		"data": [
			{
				"user_id": 1,
				"name": "Alice Johnson",
				"email": "alice@example.com",
				"phone": "+1-202-555-0134",
				"age": 24,
				"country": "US",
				"transaction_amount": 120.0,
				"is_fraud": 0
			}
		]
	}'
```

## CI/CD Pipeline

The GitHub Actions workflow at `.github/workflows/ci-cd.yml` implements push-driven CI/CD:

- Push or pull request triggers tests with coverage.
- Deployment runs only after tests pass (`needs: test`).
- Deploy step triggers Render only for pushes to `main`.

To enable deployment, add this repository secret in GitHub:

- `RENDER_DEPLOY_HOOK_URL`: Render deploy hook URL from the Render dashboard.