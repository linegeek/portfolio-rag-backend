import uvicorn

from config import PORT

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=PORT, reload=True)

