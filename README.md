# Stock Predictions with Airflow, Prophet, wandb, and GCP

This project demonstrates how to orchestrate the training and evaluation of stock price prediction models using [Facebook Prophet](https://facebook.github.io/prophet/), [Apache Airflow](https://airflow.apache.org/), [Weights & Biases (wandb)](https://wandb.ai/), and Google Cloud Storage (GCS).

## Features

- **Automated Data Download:** Fetches historical stock data from Yahoo Finance.
- **Model Training:** Trains Prophet models for multiple tickers.
- **Evaluation & Logging:** Evaluates models, logs metrics and plots to wandb.
- **Model Versioning:** Uploads models and metadata to GCS.
- **Orchestration:** Uses Airflow to schedule and manage model training workflows.
- **Dockerized:** All components run in containers for reproducibility.

---

## Project Structure

```
.
├── airflow/
│   ├── dags/
│   │   └── stock_prediction_dag.py
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   └── requirements.txt
├── src/
│   └── train_model.py
├── requirements.txt
└── README.md
```

---

## Getting Started

### 1. Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)
- Google Cloud service account with access to your GCS bucket
- [wandb](https://wandb.ai/) account and API key

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
GCS_BUCKET_NAME=your-bucket-name
PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/app/.gcp/your-service-account.json
WANDB_API_KEY=your-wandb-api-key
MODELS_DIR=models
BEST_MODEL_DIR=models/best
MODEL_RUNS_DIR=models/runs
```

Place your GCP service account JSON at the path specified above.

### 3. Build and Start Airflow

```sh
cd airflow
docker compose up --build
```

- The Airflow UI will be available at [http://localhost:8080](http://localhost:8080).
- The first time you run Airflow in standalone mode, it will print the admin credentials in the logs.

### 4. Accessing Airflow

Check the logs for the admin password:

```sh
docker compose logs airflow
```

Look for a line like:

```
Admin user created with username: admin and password: <random_password>
```

Login with these credentials.

---

## Usage

- The Airflow DAG (`stock_forecast_daily`) will run daily and train models for the tickers specified in the DAG.
- Model artifacts and metrics are logged to wandb and GCS.
- You can customize tickers and DAG schedule in `airflow/dags/stock_prediction_dag.py`.

---

## Development

- To run the training script locally:
  ```sh
  pip install -r requirements.txt
  python src/train_model.py --ticker AAPL --period 1y --forecast_periods 14
  ```

---

## Troubleshooting

- **Airflow UI not accessible?** Make sure the containers are running and port 8080 is not blocked.
- **No admin credentials?** Check the logs as described above.
- **GCS or wandb errors?** Ensure your `.env` is correct and credentials are mounted in the container.

---

## License

MIT License

---

## Acknowledgements

- [Facebook Prophet](https://facebook.github.io/prophet/)
- [Apache Airflow](https://airflow.apache.org/)
- [Weights & Biases](https://wandb.ai/)
- [Google Cloud Storage](https://cloud.google.com/storage)
- [Yahoo Finance](https://finance.yahoo.com/) 