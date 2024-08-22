from typing import Annotated, List, Literal, Optional, Text

from app.db.conversations import create_conversation
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
    conversation = conversation_create.to_conversation()
    return await crud.create_conversation(db, conversation, current_user)


@router.get("/conversations", response_model=List[Conversation])
async def api_list_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    return await crud.get_user_conversations(
        db, current_user.id, skip=skip, limit=limit
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
