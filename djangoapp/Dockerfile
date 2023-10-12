FROM python:3.7.3-alpine

# create directory for the default user
RUN mkdir -p /home/stableduel
# create the default user
RUN addgroup -S stableduel && adduser -S stableduel -G stableduel

# set workdir
WORKDIR /home/stableduel/djangoapp

# enable python logging
ENV PYTHONUNBUFFERED 1
ENV LANG en_US.utf8
ARG ENV

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements/*.txt ./requirements/

RUN curl https://sh.rustup.rs -sSf | sh
# install postgres client and runtime dependencies
RUN apk add --update --no-cache postgresql-client jpeg-dev zlib-dev &&\
# install individual dependencies for the build to save space
    apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev musl-dev python3-dev \
    libffi-dev openssl-dev libxml2-dev libxslt-dev python-dev

RUN apk add build-base

RUN --mount=type=cache,target=/root/.cache \
  if [ "$ENV" = "dev" ]; then \
    pip install -r ./requirements/local.txt; \
  else \
    pip install -r ./requirements/production.txt; \
  fi

COPY . .
# chown all the files to the stableduel user
RUN chown -R stableduel:stableduel .

COPY start.sh /start.sh
RUN chmod +x /start.sh

COPY celery_start.sh /celery_start.sh
RUN chmod +x /celery_start.sh

RUN python manage.py collectstatic

USER stableduel

# expose 8000 and start the gunicorn server
EXPOSE 8000