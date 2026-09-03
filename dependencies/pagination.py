"""
Pagination dependency (Module 16).

A single PaginationParams dependency used by every list endpoint, so
page/page_size bounds-checking lives in one place instead of being
copy-pasted into 15 different routers.
"""

from dataclasses import dataclass

from fastapi import Query

from core.config import settings


@dataclass
class PaginationParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    page_size: int = Query(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page, max {settings.MAX_PAGE_SIZE}",
    ),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def build_paginated_response(items: list, total: int, params: PaginationParams) -> dict:
    """
    Shared helper for constructing the dict a router hands to
    PaginatedResponse[...]. total_pages uses ceiling division so a
    partially-full last page still counts as a page.
    """
    total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
    }
