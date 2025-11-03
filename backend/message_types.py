from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Union, Annotated

## Base structures
class WsUserStatus(BaseModel):
    username: str
    connected_at: str

## Chat
### WebSockets protocol messages
class WsConnectionRequest(BaseModel):
    event_type: Literal["connection_request"] = "connection_request"
    username: str
class WsConnectionResponse(BaseModel):
    event_type: Literal["connection_response"] = "connection_response"
    username: str
    user_id: str
class WsConnectionReject(BaseModel):
    event_type: Literal["connection_reject"] = "connection_reject"
    response: str
class WsSystemMessage(BaseModel):
    event_type: Literal["system"] = "system"
    severity: Literal["success", "info", "warning", "error"]
    message: str
### Messaging
class WsMessageHistory(BaseModel):
    event_type: Literal["message_history"] = "message_history"
    messages: List[Dict]
class WsMessage(BaseModel):
    event_type: Literal["message"] = "message"
    username: str
    message: str
### User events
class WsTypingEvent(BaseModel):
    event_type: Literal["typing"] = "typing"
    username: str
    is_typing: bool
class WsUsersOnline(BaseModel):
    event_type: Literal["users_online"] = "users_online"
    users: List[WsUserStatus]
class WsUserJoinEvent(BaseModel):
    event_type: Literal["user_join"] = "user_join"
    username: str
class WsUserLeaveEvent(BaseModel):
    event_type: Literal["user_leave"] = "user_leave"
    username: str

### Room info and management
class RoomInfo(BaseModel):
    room_name: str
    room_creator: str
    connected_users: List[str]
class WsAllRooms(BaseModel):
    event_type: Literal["all_rooms"] = "all_rooms"
    rooms: List[RoomInfo]
class WsRoomChatClear(BaseModel):
    event_type: Literal["room_chat_clear"] = "room_chat_clear"
    username: str
    room_name: str
class WsRoomCreate(BaseModel):
    event_type: Literal["room_create"] = "room_create"
    room: RoomInfo
class WsRoomCreateReject(BaseModel):
    event_type: Literal["room_create_reject"] = "room_create_reject"
    response: str
#### Room switching, note that the client will not have switched rooms until it receives a WsRoomSwitchResponse
class WsRoomSwitchRequest(BaseModel):
    event_type: Literal["room_switch_request"] = "room_switch_request"
    room_name: str
class WsRoomSwitchResponse(BaseModel):
    event_type: Literal["room_switch_response"] = "room_switch_response"
    room_name: str
class WsRoomSwitchReject(BaseModel):
    event_type: Literal["room_switch_reject"] = "room_switch_reject"
    response: str

# The main event type, used for all WebSocket events
# The event_type field is used to denote the type of event, so it is possible to e.g.
# switch over the incoming message and determine its type on the receiver side.
WsEvent = Annotated[
    Union[
        WsConnectionRequest,
        WsConnectionResponse,
        WsConnectionReject,
        WsMessage,
        WsMessageHistory,
        WsTypingEvent,
        WsSystemMessage,
        WsUsersOnline,
        WsUserJoinEvent,
        WsUserLeaveEvent,
        WsAllRooms,
        WsRoomCreate,
        WsRoomCreateReject,
        WsRoomChatClear,
        WsRoomSwitchRequest,
        WsRoomSwitchResponse,
        WsRoomSwitchReject,
    ],
    Field(discriminator="event_type"),
]

# Pydantic models for request/response with the HTTP API
class ChatMessage(BaseModel):
    username: str
    message: str

class UserConnection(BaseModel):
    username: str

class UserConnectionResponse(BaseModel):
    response: str

class ChatData(BaseModel):
    messages: List[Dict]
    connected_users: List[Dict]

# Unimplemented for now, will be added in case more work is needed!
## Register
class WsRegisterRequest(BaseModel):
    username: str
    password: str
class WsRegisterResponse(BaseModel):
    response: str
class WsRegisterReject(BaseModel):
    response: str
# Login
class WsLoginRequest(BaseModel):
    username: str
    password: str
class WsLoginResponse(BaseModel):
    response: str
class WsLoginReject(BaseModel):
    response: str
## Groups
class WsCreateGroupRequest(BaseModel):
    group_name: str
class WsCreateGroupResponse(BaseModel):
    response: str
class WsAddUserToGroupRequest(BaseModel):
    group_name: str
    username: str
