# Use the same Python version from your devcontainer
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy your requirements first for faster building
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your ATAAA code
COPY . .

# Set the port (Google Cloud Run uses 8080 by default)
EXPOSE 8080

# Command to run your specific file
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]
