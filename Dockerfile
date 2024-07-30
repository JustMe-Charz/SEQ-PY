# Use an official Python image as a base
FROM python:3.12-slim-buster

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt ./

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port for the bot
EXPOSE 8080

# Command to run when the container starts
CMD ["python", "bot.py"]
