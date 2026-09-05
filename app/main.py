from fastapi import FastAPI


app = FastAPI(
    title="VBOND Store API",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "VBOND Store API is running"
    }

    