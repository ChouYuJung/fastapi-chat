# fastapi-chat

## API Overview

The fastapi-chat API provides a comprehensive set of endpoints for building a feature-rich chat application. It covers essential functionalities including user management, messaging, contact management, multimedia handling, notifications, and more. The API is organized into the following main categories:

1. **User Management**: Handles user authentication, registration, login, and profile management.

2. **Messaging**: Enables creating conversations, sending messages, and managing message content.

3. **Real-time Communication**: Implements WebSocket endpoints for instant message delivery and updates.

4. **Contact Management**: Allows users to add, remove, and manage their contacts, including blocking functionality.

5. **Multimedia Handling**: Provides endpoints for uploading and retrieving files such as images and documents.

6. **Notifications**: Manages push notifications to keep users informed of new messages and activities.

7. **Status and Presence**: Tracks user online status and typing indicators for enhanced user experience.

8. **Group Chat**: Offers functionality for creating and managing group conversations.

9. **Search**: Enables users to search for specific messages across conversations.

10. **Analytics**: Provides optional endpoints for gathering usage statistics and user activity data.

This API is designed to be scalable, secure, and efficient, catering to the needs of modern chat applications. It follows RESTful principles and uses standard HTTP methods for different operations. The API also includes real-time features through WebSocket integration, ensuring a responsive and interactive chat experience.

## User Management APIs

### 1. Authentication API

- POST /auth/register: Create a new user account
- POST /auth/login: Authenticate a user and generate access token
- POST /auth/logout: Log out a user and invalidate their token
- POST /auth/refresh-token: Refresh an expired access token

### 2. User Profile API

- GET /users/me: Retrieve the current user's profile information
- GET /users: List users with optional filtering and pagination
- POST /users: Create a new user
- GET /users/{user_id}: Retrieve user profile information
- PUT /users/{user_id}: Update user profile information

## Messaging APIs

### 3. Conversations API

- POST /conversations: Create a new conversation
    - Requires `ADMIN` or `EDITOR` role
    - Request body: ConversationCreate schema
    - Response: Conversation schema

- GET /conversations: Retrieve a list of conversations
    - Requires `ADMIN` or `EDITOR` role
    - Query parameters:
        - disabled: Optional[bool] - Filter by disabled status
        - sort: "asc" | "desc" | 1 | -1 - Sort order (default: "asc")
        - start: Optional[str] - Starting `conversation_id` for pagination
        - before: Optional[str] - End `conversation_id` for pagination
        - limit: Optional[int] - Number of results to return (default: 20)
    - Response: Pagination[Conversation] schema

- GET /conversations/{conversation_id}: Get details of a specific conversation
    - Requires `ADMIN` or `EDITOR` role
    - Path parameter: `conversation_id`
    - Response: Conversation schema
    - Returns 404 if conversation not found

- PUT /conversations/{conversation_id}: Update conversation details
    - Requires `ADMIN` or `EDITOR` role
    - Path parameter: `conversation_id`
    - Request body: ConversationUpdate schema
    - Response: Updated Conversation schema
    - Returns 404 if conversation not found

- DELETE /conversations/{conversation_id}: Delete a conversation
    - Requires `ADMIN` role
    - Path parameter: `conversation_id`
    - Query parameter: soft_delete (boolean, default: True)
    - Response: 204 No Content

### 4. Messages API (TODO)

- POST /conversations/{conversationId}/messages: Send a new message
- GET /conversations/{conversationId}/messages: Retrieve messages for a conversation
- PUT /messages/{messageId}: Edit a message
- DELETE /messages/{messageId}: Delete a message
- POST /messages/{messageId}/react: Add a reaction to a message

### 5. Real-time Messaging API (TODO)

- Implement WebSocket endpoints for real-time message delivery and updates

## Contact Management APIs

### 6. Contacts API (TODO)

- POST /contacts: Add a new contact
- GET /contacts: Retrieve user's contact list
- DELETE /contacts/{contactId}: Remove a contact
- PUT /contacts/{contactId}/block: Block a contact
- PUT /contacts/{contactId}/unblock: Unblock a contact

## Multimedia APIs

### 7. File Upload API (TODO)

- POST /upload: Upload files (images, documents, etc.)
- GET /files/{fileId}: Retrieve file information or download file

## Notification APIs

### 8. Push Notification API (TODO)

- POST /notifications/register-device: Register a device for push notifications
- POST /notifications/send: Send a push notification to a user or group of users

## Status and Presence APIs

### 9. User Status API (TODO)

- PUT /users/{userId}/status: Update user's online status
- GET /users/{userId}/status: Get a user's current status

### 10. Typing Indicator API (TODO)

- POST /conversations/{conversationId}/typing: Indicate user is typing
- DELETE /conversations/{conversationId}/typing: Indicate user stopped typing

## Group Chat APIs

### 11. Group Management API (TODO)

- POST /groups: Create a new group
- GET /groups/{groupId}: Get group details
- PUT /groups/{groupId}: Update group information
- DELETE /groups/{groupId}: Delete a group
- POST /groups/{groupId}/members: Add members to a group
- DELETE /groups/{groupId}/members/{userId}: Remove a member from a group

## Search APIs

### 12. Message Search API (TODO)

- GET /search/messages: Search for messages across conversations

## Analytics APIs (Optional)

### 13. Usage Analytics API (TODO)

- GET /analytics/messages: Get message statistics
- GET /analytics/users: Get user activity statistics
