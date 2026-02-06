"""Financial reports router definitions."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/reports/retrieve")
async def retrieve_reports() -> str:
    """Endpoint to retrieve financial reports."""
    raise NotImplementedError
