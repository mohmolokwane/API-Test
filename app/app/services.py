import os
import httpx
from typing import List
from fastapi import HTTPException
from app.models import GistResponse, GistFile

GITHUB_API_BASE = os.getenv("GITHUB_API_URL", "https://api.github.com")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PER_PAGE = 100
MAX_PAGES = 10  # Safety cap to prevent runaway requests & respect rate limits

async def fetch_user_gists(username: str) -> List[GistResponse]:
    url = f"{GITHUB_API_BASE}/users/{username}/gists"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GistsAPI/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    async with httpx.AsyncClient() as client:
        all_raw_gists = []
        page = 1

        while page <= MAX_PAGES:
            response = await client.get(url, params={"per_page": PER_PAGE, "page": page}, headers=headers)

            # Explicit GitHub API error handling
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"GitHub user '{username}' not found.")
            if response.status_code in (403, 429):
                raise HTTPException(status_code=503, detail="GitHub API rate limit exceeded. Please try again later.")
            if response.status_code >= 500:
                raise HTTPException(status_code=502, detail="GitHub API is currently unavailable. Please try again later.")
            
            response.raise_for_status()

            data = response.json()
            if not data:
                break  # Empty page means we're done

            all_raw_gists.extend(data)

            # GitHub pagination uses Link header. Stop if no 'next' relation.
            link_header = response.headers.get("Link", "")
            if 'rel="next"' not in link_header:
                break

            page += 1

    return [_map_gist_to_model(gist) for gist in all_raw_gists]

def _map_gist_to_model(raw_gist: dict) -> GistResponse:
    files = [
        GistFile(
            filename=f.get("filename", "unknown"),
            size=f.get("size", 0),
            language=f.get("language")
        )
        for f in raw_gist.get("files", {}).values()
    ]
    return GistResponse.model_validate({
        "id": raw_gist["id"],
        "description": raw_gist.get("description"),
        "html_url": raw_gist.get("html_url", ""),
        "created_at": raw_gist["created_at"],
        "files": files
    })