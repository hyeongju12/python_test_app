# set base image (host OS)
FROM python:3.8

# set the working directory in the container
WORKDIR /app

# copy the dependencies file to the working directory
COPY . .

# install dependencies
RUN pip install -r requirements.txt

# expose port
EXPOSE 5002

# command to run on container start
CMD ["python", "./app.py" ]