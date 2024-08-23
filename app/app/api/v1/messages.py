from typing import Literal, Optional, Text

from app.db.messages import (
    create_message,
    delete_message,
    list_messages,
    retrieve_message,
    update_message,
)
from app.deps.oauth import RoleChecker
from app.schemas.messages import Message, MessageCreate, MessageUpdate
from app.schemas.oauth import Role
from app.schemas.pagination import Pagination
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response

router = APIRouter()


@router.get(
    "/conversations/{conversation_id}/messages",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    response_model=Pagination[Message],
)
async def api_list_messages(
    conversation_id: Text = Path(..., description="ID of the conversation"),
    sort: Literal["asc", "desc", 1, -1] = Query("desc", description="Sort order"),
    start: Optional[Text] = Query(
        None, description="Starting message ID for pagination"
    ),
    before: Optional[Text] = Query(None, description="End message ID for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Number of messages to return"),
) -> Pagination[Message]:
    """Retrieve messages for a specific conversation."""

    return Pagination[Message].model_validate(
        list_messages(
            conversation_id=conversation_id,
            sort=sort,
            start=start,
            before=before,
            limit=limit,
        ).model_dump()
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    response_model=Message,
    status_code=201,
)
async def api_create_message(
    conversation_id: Text = Path(..., description="ID of the conversation"),
    message_create: MessageCreate = Body(...),
) -> Message:
    """Create a new message in a conversation."""

    message = message_create.to_message()
    created_message = create_message(conversation_id=conversation_id, message=message)
    if created_message is None:
        raise HTTPException(status_code=400, detail="Failed to create message")
    return created_message


@router.get(
    "/conversations/{conversation_id}/messages/{message_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    response_model=Message,
)
async def api_retrieve_message(
    conversation_id: Text = Path(..., description="ID of the conversation"),
    message_id: Text = Path(..., description="ID of the message"),
) -> Message:
    """Retrieve a specific message by its ID."""

    message = retrieve_message(conversation_id=conversation_id, message_id=message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.put(
    "/conversations/{conversation_id}/messages/{message_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    response_model=Message,
)
async def api_update_message(
    conversation_id: Text = Path(..., description="ID of the conversation"),
    message_id: Text = Path(..., description="ID of the message"),
    message_update: MessageUpdate = Body(...),
) -> Message:
    """Update an existing message."""

    updated_message = update_message(
        conversation_id=conversation_id,
        message_id=message_id,
        message_update=message_update,
    )
    if updated_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return updated_message


@router.delete(
    "/conversations/{conversation_id}/messages/{message_id}",
    dependencies=[Depends(RoleChecker([Role.ADMIN, Role.EDITOR]))],
    status_code=204,
)
async def api_delete_message(
    conversation_id: Text = Path(..., description="ID of the conversation"),
    message_id: Text = Path(..., description="ID of the message"),
    soft_delete: bool = Query(True, description="Perform a soft delete if True"),
):
    """Delete a message (soft delete by default)."""

    success = delete_message(
        conversation_id=conversation_id, message_id=message_id, soft_delete=soft_delete
    )
    if success is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return Response(status_code=204)
