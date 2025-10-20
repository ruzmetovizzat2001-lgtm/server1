FROM python:3.10-slim

WORKDIR /server1

COPY server1.py .

EXPOSE 8080

CMD ["python", "server1.py"]

