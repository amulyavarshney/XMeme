import uvicorn

from src.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("src.main:app", host="0.0.0.0", port=8081, reload=True)
