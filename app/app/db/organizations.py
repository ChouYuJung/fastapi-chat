from typing import TYPE_CHECKING, Literal, Optional, Text

from app.schemas.oauth import Organization, OrganizationCreate, OrganizationUpdate
from app.schemas.pagination import Pagination
from app.utils.common import run_as_coro

if TYPE_CHECKING:
    from app.db._base import DatabaseBase


async def list_organizations(
    db: "DatabaseBase",
    *,
    disabled: Optional[bool] = False,
    sort: Literal["asc", "desc"] = "asc",
    start: Optional[Text] = None,
    before: Optional[Text] = None,
    limit: Optional[int] = 10,
) -> Pagination[Organization]:
    return await run_as_coro(
        db.list_organizations,
        disabled=disabled,
        sort=sort,
        start=start,
        before=before,
        limit=limit,
    )


async def create_organization(
    db: "DatabaseBase",
    *,
    organization_create: OrganizationCreate,
    owner_id: Text,
) -> Optional[Organization]:
    return await run_as_coro(
        db.create_organization,
        organization_create=organization_create,
        owner_id=owner_id,
    )


async def update_organization(
    db: "DatabaseBase",
    *,
    organization_id: Text,
    organization_update: OrganizationUpdate,
) -> Optional[Organization]:
    return await run_as_coro(
        db.update_organization,
        organization_id=organization_id,
        organization_update=organization_update,
    )


async def retrieve_organization(
    db: "DatabaseBase",
    *,
    organization_id: Text,
) -> Optional[Organization]:
    return await run_as_coro(db.retrieve_organization, organization_id)


async def delete_organization(
    db: "DatabaseBase",
    *,
    organization_id: Text,
    soft_delete: bool = True,
) -> Optional[Organization]:
    return await run_as_coro(
        db.delete_organization, organization_id=organization_id, soft_delete=soft_delete
    )
