from fastapi import FastAPI
import logging, json, os, time

logger = logging.getLogger("api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'))
logger.addHandler(handler)

app = FastAPI()

@app.get("/health")
def health():
    logger.info("Health check endpoint called")
    return {"status": "ok", "env": os.getenv("APP_ENV", "DEV")}