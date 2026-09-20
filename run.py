"""Start the Scheme Saathi server:  python run.py  (then open http://localhost:8000)"""
import uvicorn

from app.core import config

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False)
