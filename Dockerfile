FROM python:3.11-slim

WORKDIR /app
COPY server1.py ./

EXPOSE 8080
EXPOSE 9000

ENV PYTHONUNBUFFERED=1

CMD ["python", "server1.py"]
