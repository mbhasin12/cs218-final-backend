FROM python:3.11-slim


WORKDIR /app
COPY . /app


RUN pip3 install --no-cache-dir -r requirements.txt


EXPOSE 80

CMD ["python3", "app.py"]