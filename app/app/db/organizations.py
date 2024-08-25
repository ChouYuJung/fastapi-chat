from typing import TYPE_CHECKING, Literal, Optional, Text

from app.schemas.oauth import Organization, OrganizationCreate, OrganizationUpdate
from app.schemas.pagination import Pagination

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
    pass


async def create_organization(
    db: "DatabaseBase",
    *,
    organization_create: OrganizationCreate,
    owner_id: Text,
) -> Organization:
    pass


async def update_organization(
    db: "DatabaseBase",
    *,
    organization_id: Text,
    organization_update: OrganizationUpdate,
) -> Organization:
    pass


async def retrieve_organization(
    db: "DatabaseBase",
    *,
    organization_id: Text,
) -> Optional[Organization]:
    pass


async def delete_organization(
    db: "DatabaseBase",
    *,
    organization_id: Text,
    soft_delete: bool = True,
) -> Optional[Organization]:
    pass
