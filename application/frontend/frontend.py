from fastapi import FastAPI

app = FastAPI()


@app.get("/users/count")
async def user_count():
    return dict(count=0);