FROM python:3.13-slim

WORKDIR /exploit

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flags.py .
COPY solve.py .
CMD ["python", "-u", "solve.py"]
