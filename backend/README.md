This is the Application Backend.

* **SQLAlchemy** models (independent of Flask extensions, so they can be used with Celery workers directly).
* **CORS** (Cross Origin Resource Sharing).
* **REST API** for get, post and patch requests.
* **Swagger UI** Documentation provide by Swagger UI using endpoint `/`
* **DOCUMENTATION** interactive API doc using endpoint `/doc`

## Local Run

```bash
cd backend
python3 app.py
```

## Deployment

After signing up on Heroku, create a new app, and proceed to download Heroku CLI

```bash
heroku login -i
heroku builds:create -a varamu-xmeme
```
Running on Python web server using Uvicorn and Gunicorn.