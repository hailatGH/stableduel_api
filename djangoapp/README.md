[![Codeship Status for apaxsoftware/apax-drupal](https://app.codeship.com/projects/a414c780-e139-0136-0e76-66b152ecac3d/status?branch=master)](https://app.codeship.com/projects/318732)

# Stable Duel API

Document spinning up, creating admin user, connecting to Auth0, testing and deploying

## AWS setup

General overview:
Load Balancer -> VPC -> EC2 -> nginx/gunicorn/django.service

- Connect to prod / db - Use the `sd-api-dev.pem` and `sd-api-prod.pem` from **OnePassword** with user **ubuntu**

  ```bash
  ssh -i ~/.ssh/sd-api-prod.pem ubuntu@<ec2-public-ip>
  ```

## Local Development (with Docker)

- **Overview** -
  We use docker with docker compose as rochestrating tool. For now we build the 4 main services (there may be more, related to the wagering):

  1. `db` (Postgresql) - we may use the azurecr dev one, but it can be changed to a standard `postgres:alpine`
  2. `api` (the django API) - standard build from the Dockerfile in the djangoapp/, using the `start.sh` script
  3. `celery` (python based task queue worker) - we use the same context from djangoapp/ with the same Dockerfile, but differnet `celery_start.sh` script. It also runs the celery beat (simple scheduler) in the same container, instead of separate service, because we have very few scheduled tasks for now.
  4. `redis` - Used for cache for the api and as message brocker for celery. For now it's configured to use the azurecr, but it can be changed to standard `redis:alpine`

- Running the project

  ```bash
  docker compose up --build
  ```

  The `--build` flag will create new image, so if you want to skip this part and just build a container from the last existing image, dont use it.
  Also the container is linked to the current given context, i.e. the djangoapp/ code, via the `volume` argument, which syncs any code changes for the api (besides Dockerfile and docker-compose.yml) in real time.

- Communication with the `scus` (Azure .NET) api - for now it's hooked to the qa api, via the `CHRIMS_BASE_URL=https://qa-sd-scus-api.azurewebsites.net/api/` variable in the .env file, but it's not tested.

- Environment variables
  The `.env` file is left in version control, even tho it's not a good practice, until we can put the content in a secure service, from which we can obtain it. And since this was missing previously, we had to find out which variables we need, basically one by one.
  Currently the `.env` points to the azure services and the `.env.local` points to localhost. (if we want to use `postgres:alpine` and `redis:alpine`)

- Auth0 settings
  - The .env variable `AUTH_AUDIENCE` must point to the `CLIENT_ID` of the main application (**StableDuel**)
  - The .env variable `AUTH_ISSUER` points to the main auth0 domain (**https://stableduel.auth0.com/**)

## Chef / Vagrant

The Chef + Vagrant setup was deprecated a while ago and it's unusable on UNIX based environemnt. It's possible that it may run on Windows, but the package versions in it are versions that are older that what exists on AWS dev / prod. The docker-compose + Docker solution is way more sustainable and actually works.

## Potential Build Problems

- There's a chance to encounter encoding issues when dealing with files edited on windows based OS and then transfered to Unix based one. This may result in the docker container not being able to find a file (for example /start.sh), even though it's there, because it has windows encoded characters in it. The solution would be using tools like `dos2unix` and running it on top level of the project to get rid of all windows encoded characters:
  ```bash
  find . -type f -print0 | xargs -0 dos2unix
  ```
- Sometimes docker caches things way "too hard" and new changes are not reflected in the latest image (for example celery beat may start throwin permission errors, for files already existing). In those cases the best thing to do is to rebuild the image with no cache and start (up) it like:
  ```bash
  docker compose build --no-cache <service_name>
  docker compose up --force-recreate <service_name>
  ```
