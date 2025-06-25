from fastapi import FastAPI

app = FastAPI(title="Lambda.hu Építőanyag AI Rendszer")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Lambda.hu AI API"} 