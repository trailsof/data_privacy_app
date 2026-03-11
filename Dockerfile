# we need
# dependencies
# - flask
# python installed
# populate the db
# run the app (e.g. flask run)

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# read requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the project files into the container
COPY . .

# set environment for flask seed
ENV FLASK_APP=web_app/common_app_dashboard.py

# run the flask app with something like   app.run(debug=True, port=5000)
# lets try with 80 after to see if it breaks :)
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]