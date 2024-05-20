# Use Python 3.10 as the main version
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
ENV PORT 8080
WORKDIR $APP_HOME
COPY . ./

# Install system-level dependencies
# RUN apt-get update && apt-get install -y
RUN apt-get update && apt-get install libgl1 -y
RUN apt-get install libglib2.0-0 -y
RUN apt-get install libxrender1 -y
RUN apt-get install libxi6 libsm6 -y
RUN apt-get install libxkbcommon0 -y
RUN apt-get install libgomp1 -y

# Install any dependencies specified in requirements.txt
RUN pip install -r requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
# CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app