from typing import Literal, Optional, Text

from app.db._base import DatabaseBase
from app.db.organizations import (
    create_organization,
    delete_organization,
    list_organizations,
    retrieve_organization,
    update_organization,
)
from app.deps.db import depend_db
from app.deps.oauth import (
    TYPE_TOKEN_PAYLOAD_DATA_USER,
    TYPE_TOKEN_PAYLOAD_DATA_USER_ORG,
    PermissionChecker,
    get_user_of_org_with_required_permissions,
    get_user_with_required_permissions,
)
from app.schemas.oauth import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    Permission,
)
from app.schemas.pagination import Pagination
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status

router = APIRouter()


@router.get(
    "/organizations",
    dependencies=[Depends(PermissionChecker([Permission.MANAGE_ORGANIZATIONS]))],
)
async def api_list_organizations(
    disabled: Optional[bool] = Query(False),
    sort: Literal["asc", "desc"] = Query("asc"),
    start: Optional[Text] = Query(None),
    before: Optional[Text] = Query(None),
    limit: Optional[int] = Query(10, ge=1, le=100),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[Organization]:
    """Search for organizations by name or other criteria."""

    return await list_organizations(
        db, disabled=disabled, sort=sort, start=start, before=before, limit=limit
    )


@router.post("/organizations")
async def api_create_organization(
    organization_create: OrganizationCreate = Body(...),
    token_payload_data_user: TYPE_TOKEN_PAYLOAD_DATA_USER = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORGANIZATIONS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Create a new organization."""

    user = token_payload_data_user[3]
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
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORG_CONTENT])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Retrieve an organization by its ID."""

    org_id = token_payload_data_user_org[4]

    org = await retrieve_organization(db, organization_id=org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )
    return org


@router.put("/organizations/{org_id}")
async def api_update_organization(
    organization_update: OrganizationUpdate = Body(...),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_of_org_with_required_permissions([Permission.MANAGE_ORG_CONTENT])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Update an organization by its ID."""

    org_id = token_payload_data_user_org[4]

    org = await update_organization(
        db, organization_id=org_id, organization_update=organization_update
    )
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    return org


@router.delete("/organizations/{org_id}")
async def api_delete_organization(
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORGANIZATIONS])
    ),
    db: DatabaseBase = Depends(depend_db),
):
    """Delete an organization by its ID."""

    org_id = token_payload_data_user_org[4]

    await delete_organization(db, organization_id=org_id, soft_delete=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
