FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# development
#ENTRYPOINT ["python"]
#CMD ["./run.py"]

#deployment, start uWSGI
CMD ["uwsgi", "app.ini"]

