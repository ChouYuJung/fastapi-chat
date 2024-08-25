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
from app.deps.oauth import PermissionChecker, get_user_with_required_permissions
from app.schemas.oauth import (
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    Permission,
    User,
)
from app.schemas.pagination import Pagination
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, Response, status

router = APIRouter()


async def _retrieve_organization_with_user_permission(
    db: "DatabaseBase", *, org_id: Text, user: "User"
) -> "Organization":
    """Retrieve an organization by its ID with user permission checking."""

    org = await retrieve_organization(db, organization_id=org_id)

    # Check if the organization exists
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if the current user has permission to access the organization
    if user is not None and user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this organization",
        )

    return org


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
    current_user: User = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORGANIZATIONS])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Create a new organization."""

    return await create_organization(
        db, organization_create=organization_create, owner_id=current_user.id
    )


@router.get("/organizations/{org_id}")
async def api_retrieve_organization(
    org_id: Text = QueryPath(
        ..., description="The ID of the organization to retrieve."
    ),
    current_user: User = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORG_CONTENT])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Retrieve an organization by its ID."""

    org = await _retrieve_organization_with_user_permission(
        db, org_id=org_id, user=current_user
    )
    return org


@router.put("/organizations/{org_id}")
async def api_update_organization(
    org_id: Text = QueryPath(..., description="The ID of the organization to update."),
    organization_update: OrganizationUpdate = Body(...),
    current_user: User = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORG_CONTENT])
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Organization:
    """Update an organization by its ID."""

    org = await _retrieve_organization_with_user_permission(
        db, org_id=org_id, user=current_user
    )

    org = await update_organization(
        db, organization_id=org_id, organization_update=organization_update
    )

    return org


@router.delete("/organizations/{org_id}")
async def api_delete_organization(
    org_id: Text = QueryPath(..., description="The ID of the organization to delete."),
    current_user: User = Depends(
        get_user_with_required_permissions([Permission.MANAGE_ORGANIZATIONS])
    ),
    db: DatabaseBase = Depends(depend_db),
):
    """Delete an organization by its ID."""

    await _retrieve_organization_with_user_permission(
        db, org_id=org_id, user=current_user
    )

    await delete_organization(db, organization_id=org_id, soft_delete=True)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
