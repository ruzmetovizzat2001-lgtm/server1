FROM python:3.11-slim

WORKDIR /app
COPY server1.py ./

EXPOSE 10000
EXPOSE 9000

CMD ["python", "server1.py"]
