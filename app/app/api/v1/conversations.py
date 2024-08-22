from typing import Annotated, List, Literal, Optional, Text

from app.db.conversations import (
    create_conversation,
    fake_conversations_db,
    fake_user_conversations_db,
    list_conversations,
)
from app.db.users import create_user as create_db_user
from app.db.users import get_user_by_id
from app.db.users import list_users as list_db_users
from app.db.users import update_user as update_db_user
from app.deps.oauth import RoleChecker, get_current_active_user, get_current_user
from app.schemas.conversations import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
)
from app.schemas.oauth import Role, User, UserCreate, UserUpdate
from app.schemas.pagination import Pagination
from app.utils.oauth import get_password_hash
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi import Path as QueryPath
from fastapi import Query, status

router = APIRouter()


@router.post(
    "/conversations",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    response_model=Conversation,
)
async def api_create_conversation(conversation_create: ConversationCreate):
    """Create a new conversation."""

    conversation = conversation_create.to_conversation()
    create_conversation(fake_conversations_db, conversation=conversation)
    return conversation


@router.get(
    "/conversations",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    response_model=List[Conversation],
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
        list_conversations(
            disabled=disabled,
            sort=sort,
            start=start,
            before=before,
            limit=limit,
        ).model_dump()
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def api_get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    conversation = await crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.id not in [p.user_id for p in conversation.participants]:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this conversation"
        )
    return conversation


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def api_update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    conversation = await crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.id not in [p.user_id for p in conversation.participants]:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this conversation"
        )
    return await crud.update_conversation(db, conversation_id, conversation_update)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def api_delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    conversation = await crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if current_user.id not in [p.user_id for p in conversation.participants]:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this conversation"
        )
    await crud.delete_conversation(db, conversation_id)
