from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def user_count():
    return
