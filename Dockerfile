# Dockerfile

FROM python:3.9-slim
RUN apt-get update && apt-get install -y libportaudio2 libasound2 ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]