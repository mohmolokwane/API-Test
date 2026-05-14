from fastapi import FastAPI
from app.routes import router
import uvicorn

app = FastAPI(
    title="GitHub Gists API",
    description="Interacts with GitHub API to fetch public user gists",
    version="1.0.0"
)

app.include_router(router, tags=["Gists"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, log_level="info")