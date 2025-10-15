from threading import Thread

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
	return {"message": "Server is Online."}

def start(port=8000):
	uvicorn.run(app, host="0.0.0.0", port=port)

def server_thread(port=8000):
	t = Thread(target=start, args=(port,))
	t.start()