# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY . .

# install dependencies
RUN pip install -r requirements.txt

RUN opentelemetry-bootstrap --action=install
# copy the content of the local src directory to the working directory

ENV TRACES_EXPORTER=console,otlp
ENV METRICES_EXPORTER=otlp
ENV OTEL_SERVICE_NAME=flask-app
ENV OTEL_PYTHON_LOG_CORRELATION=true
ENV OTEL_PYTHON_LOG_LEVEL=debug
# command to run on container start
CMD [ "opentelemetry-instrument", "python", "./app.py" ]

# expose port
EXPOSE 5002
