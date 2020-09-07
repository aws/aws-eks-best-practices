# Python image to use.
FROM python:3.7

# Set the working directory to /app
WORKDIR /src

# copy the requirements file used for dependencies

COPY requirements.txt .
# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
# RUN pip install pyinstaller

# Copy the rest of the working directory contents into the container at /app
COPY . .

ENV AWS_DEFAULT_REGION=us-west-2

# Run app.py when the container launches
ENTRYPOINT [ "python", "main.py" ]