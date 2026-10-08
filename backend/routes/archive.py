"""GET /api/archive - English text

English textpage=1&pageSize=20
English text{ ok, list, total, page, pageSize }
"""

from typing import Any, Dict

from fastapi import APIRouter

from backend import db

router = APIRouter()


@router.get("/api/archive")
def get_archive(page: int = 1, pageSize: int = 20) -> Dict[str, Any]:
    """English textEnglish text createdAt English text

    - page English text 1 English textpageSize English text 20
    - English textEnglish text mock English text
    """
    if page < 1:
        page = 1
    if pageSize < 1:
        pageSize = 20
    offset = (page - 1) * pageSize
    items = db.list_decisions(limit=pageSize, offset=offset)
    total = db.count_decisions()
    return {
        "ok": True,
        "list": items,
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }
