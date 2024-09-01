from typing import Annotated, Literal, Optional, Text

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, Response, status

from fastapi_chat.db._base import DatabaseBase
from fastapi_chat.db.conversations import (
    create_conversation,
    delete_conversation,
    list_conversations,
    retrieve_conversation,
    update_conversation,
)
from fastapi_chat.deps.db import depend_db
from fastapi_chat.deps.oauth import TYPE_TOKEN_PAYLOAD_DATA_USER_ORG
from fastapi_chat.deps.oauth import Permission as Per
from fastapi_chat.deps.oauth import UserPermissionChecker
from fastapi_chat.schemas.conversations import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
)
from fastapi_chat.schemas.pagination import Pagination

router = APIRouter()


@router.get("/organizations/{org_id}/conversations/me")
async def api_list_my_conversations(
    disabled: Optional[bool] = Query(default=None),
    sort: Literal["asc", "desc", 1, -1] = Query(default="asc"),
    start: Optional[Text] = Query(default=None),
    before: Optional[Text] = Query(default=None),
    limit: Optional[int] = Query(default=20),
    token_payload_data_user_org: TYPE_TOKEN_PAYLOAD_DATA_USER_ORG = Depends(
        UserPermissionChecker([Per.USE_ORG_CONTENT], "org_user")
    ),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[Conversation]:
    """List conversations from the database."""

    user = token_payload_data_user_org[3]
    org = token_payload_data_user_org[4]
    if user.organization_id != org.id:
        raise HTTPException(status_code=403, detail="User not in organization")
    return Pagination[Conversation].model_validate(
        (
            await list_conversations(
                db,
                participants=[user.id],
                disabled=disabled,
                sort=sort,
                start=start,
                before=before,
                limit=limit,
            )
        ).model_dump()
    )


@router.post(
    "/organizations/{org_id}/conversations",
    dependencies=[Depends(UserPermissionChecker([Per.MANAGE_ORG_USERS], "org_user"))],
)
async def api_create_conversation(
    conversation_create: ConversationCreate,
    db: DatabaseBase = Depends(depend_db),
) -> Conversation:
    """Create a new conversation."""

    return await create_conversation(db, conversation_create=conversation_create)


@router.get(
    "/organizations/{org_id}/conversations",
    dependencies=[Depends(UserPermissionChecker([Per.MANAGE_ORG_USERS], "org_user"))],
)
async def api_list_conversations(
    disabled: Optional[bool] = Query(default=None),
    sort: Literal["asc", "desc", 1, -1] = Query(default="asc"),
    start: Optional[Text] = Query(default=None),
    before: Optional[Text] = Query(default=None),
    limit: Optional[int] = Query(default=20),
    db: DatabaseBase = Depends(depend_db),
) -> Pagination[Conversation]:
    """List conversations from the database."""

    return Pagination[Conversation].model_validate(
        (
            await list_conversations(
                db,
                disabled=disabled,
                sort=sort,
                start=start,
                before=before,
                limit=limit,
            )
        ).model_dump()
    )


@router.get(
    "/organizations/{org_id}/conversations/{conversation_id}",
    dependencies=[Depends(UserPermissionChecker([Per.MANAGE_ORG_USERS], "org_user"))],
)
async def api_get_conversation(
    conversation_id: Annotated[Text, QueryPath(...)],
    db: DatabaseBase = Depends(depend_db),
) -> Conversation:
    """Retrieve a conversation by ID."""

    conversation = await retrieve_conversation(db, conversation_id=conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.put(
    "/organizations/{org_id}/conversations/{conversation_id}",
    dependencies=[Depends(UserPermissionChecker([Per.MANAGE_ORG_USERS], "org_user"))],
    response_model=Conversation,
)
async def api_update_conversation(
    conversation_id: Annotated[Text, QueryPath(...)],
    conversation_update: ConversationUpdate,
    db: DatabaseBase = Depends(depend_db),
) -> Conversation:
    """Update an existing conversation."""

    conversation = await update_conversation(
        db,
        conversation_id=conversation_id,
        conversation_update=conversation_update,
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete(
    "/organizations/{org_id}/conversations/{conversation_id}",
    dependencies=[Depends(UserPermissionChecker([Per.MANAGE_ORG_USERS], "org_user"))],
)
async def api_delete_conversation(
    conversation_id: Annotated[Text, QueryPath(...)],
    soft_delete: bool = Query(default=True),
    db: DatabaseBase = Depends(depend_db),
):
    """Delete a conversation"""

    await delete_conversation(
        db, conversation_id=conversation_id, soft_delete=soft_delete
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
