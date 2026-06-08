FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt streamlit
COPY app_frontend.py .
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app_frontend.py", "--server.port=8501", "--server.address=0.0.0.0"]