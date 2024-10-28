FROM python:3.11

WORKDIR /code

COPY ./server_requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./app /code/app

ENV CONFIG_FILE_PATH=/code/app/server_config.yaml

EXPOSE 9300

CMD ["uvicorn", "app.server:app", "--port", "9300", "--host", "0.0.0.0"]