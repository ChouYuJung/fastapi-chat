from typing import Literal, Optional, Text

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status

from ..db._base import DatabaseBase
from ..db.organizations import (
    create_organization,
    delete_organization,
    list_organizations,
    update_organization,
)
from ..deps.db import depend_db
from ..deps.oauth import DependsUserPermissions, TokenOrgDepends, TokenUserDepends
from ..schemas.organizations import Organization, OrganizationCreate, OrganizationUpdate
from ..schemas.pagination import Pagination
from ..schemas.permissions import Permission

router = APIRouter()


@router.get("/organizations")
async def api_list_organizations(
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    token_payload_user: TokenUserDepends = Depends(
        DependsUserPermissions([Permission.READ_ORG], "depends_active_user")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[Organization]:
    """Search for organizations by name or other criteria."""

    querying_organization_id = None
    if token_payload_user.user.organization_id is not None:
        querying_organization_id = token_payload_user.user.organization_id

    return await list_organizations(
        db,
        organization_id=querying_organization_id,
        disabled=disabled,
        sort=sort,
        start=start,
        before=before,
        limit=limit,
    )


@router.post("/organizations")
async def api_create_organization(
    organization_create: OrganizationCreate = Body(...),
    token_payload_user: TokenUserDepends = Depends(
        DependsUserPermissions([Permission.CREATE_ORG], "depends_active_user")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Create a new organization."""

    user = token_payload_user.user
    org = await create_organization(
        db, organization_create=organization_create, owner_id=user.id
    )
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Organization already exists"
        )

    return org


@router.get("/organizations/{org_id}")
async def api_retrieve_organization(
    token_payload_org: TokenOrgDepends = Depends(
        DependsUserPermissions([Permission.READ_ORG], "depends_org_managing")
    )
) -> Organization:
    """Retrieve an organization by its ID."""

    org = token_payload_org.organization
    return org


@router.put("/organizations/{org_id}")
async def api_update_organization(
    organization_update: OrganizationUpdate = Body(...),
    token_payload_org: TokenOrgDepends = Depends(
        DependsUserPermissions([Permission.UPDATE_ORG], "depends_org_managing")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Update an organization by its ID."""

    org = token_payload_org.organization
    updated_org = await update_organization(
        db, organization_id=org.id, organization_update=organization_update
    )
    if updated_org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return updated_org


@router.delete("/organizations/{org_id}")
async def api_delete_organization(
    token_payload_org: TokenOrgDepends = Depends(
        DependsUserPermissions([Permission.DELETE_ORG], "depends_org_managing")
    ),
    db: DatabaseBase = Depends(depend_db),
):
    """Delete an organization by its ID."""

    org = token_payload_org.organization

    await delete_organization(db, organization_id=org.id, soft_delete=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
