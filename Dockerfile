FROM python:3.10-alpine

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./application /code/application
COPY ./main.py /code/

ENTRYPOINT ["python", "-u", "/code/main.py"]
