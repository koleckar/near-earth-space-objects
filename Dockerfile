FROM python:3.10

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENTRYPOINT ["python"]
CMD ["./run.py"]
