"""Chat router definitions."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/chat")
async def chat() -> dict[str, str]:
    """Chat endpoint placeholder."""
    return {"message": "Chat endpoint is under construction."}
