FROM apache/airflow:slim-3.0.2-python3.11

# Install additional dependencies if needed (e.g. yfinance, prophet)
USER root
RUN apt-get update && apt-get install -y gcc libglib2.0-0 libgl1-mesa-glx
# Set the correct user
USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt


# Don't need mounted in compose file
# COPY ../src /app/src

# Copy DAGs into Airflow DAGs directory
COPY airflow/dags/ /opt/airflow/dags/


