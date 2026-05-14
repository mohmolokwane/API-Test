from fastapi import APIRouter
from app.services import fetch_user_gists
from app.models import GistResponse

router = APIRouter()

@router.get(
    "/{username}",
    response_model=list[GistResponse],
    tags=["Gists"],
    summary="List user's public Gists",
    description="Fetches all publicly available Gists for a given GitHub username."
)
async def get_user_gists(username: str):
    # Service handles all HTTPExceptions; only success path returns here
    return await fetch_user_gists(username)