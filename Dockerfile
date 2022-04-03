FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./application /code/application
COPY ./main.py /code/

ENTRYPOINT ["python", "/code/main.py"]
