FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pyproject.toml README.md ./
COPY cryptolab ./cryptolab
COPY app ./app
COPY docs ./docs
COPY bob-sessions ./bob-sessions
COPY .streamlit ./.streamlit

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
