from typing import Annotated, Literal, Optional, Text

from app.db.conversations import (
    create_conversation,
    delete_conversation,
    fake_conversations_db,
    list_conversations,
    retrieve_conversation,
    update_conversation,
)
from app.deps.oauth import TYPE_TOKEN_PAYLOAD_DATA_USER_ORG
from app.deps.oauth import Permission as Per
from app.deps.oauth import UserPermissionChecker
from app.schemas.conversations import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
)
from app.schemas.pagination import Pagination
from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, Response, status

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
) -> Pagination[Conversation]:
    """List conversations from the database."""

    user = token_payload_data_user_org[3]
    org = token_payload_data_user_org[4]
    if user.organization_id != org.id:
        raise HTTPException(status_code=403, detail="User not in organization")
    return Pagination[Conversation].model_validate(
        (
            await list_conversations(
                fake_conversations_db,
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
) -> Conversation:
    """Create a new conversation."""

    conversation = conversation_create.to_conversation()
    await create_conversation(fake_conversations_db, conversation=conversation)
    return conversation


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
) -> Pagination[Conversation]:
    """List conversations from the database."""

    return Pagination[Conversation].model_validate(
        (
            await list_conversations(
                fake_conversations_db,
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
) -> Conversation:
    """Retrieve a conversation by ID."""

    conversation = await retrieve_conversation(
        fake_conversations_db, conversation_id=conversation_id
    )
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
) -> Conversation:
    """Update an existing conversation."""

    conversation = await update_conversation(
        fake_conversations_db,
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
):
    """Delete a conversation"""

    await delete_conversation(
        fake_conversations_db, conversation_id=conversation_id, soft_delete=soft_delete
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
