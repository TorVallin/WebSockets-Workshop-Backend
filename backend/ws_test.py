import pytest
from pydantic import ValidationError, TypeAdapter
from contextlib import contextmanager, ExitStack
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession
from server import app
from message_types import *
from websocket_handlers import GLOBAL_ROOM_NAME

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@contextmanager
def ws_for(client: TestClient, username: str, room_name: str = GLOBAL_ROOM_NAME):
    url = f"/ws"
    if room_name != GLOBAL_ROOM_NAME:
        url = f"/ws/{room_name}"
    with client.websocket_connect(url) as ws:
        ws.send_text(WsConnectionRequest(username=username).model_dump_json())
        try:
            if room_name != GLOBAL_ROOM_NAME:
                room_create = WsRoomCreate.model_validate_json(ws.receive_text())
                assert room_create.room.room_name == room_name

            response = WsConnectionResponse.model_validate_json(ws.receive_text())
            assert response.username == username
            rooms = WsAllRooms.model_validate_json(ws.receive_text())
            assert rooms.rooms[0].room_name == GLOBAL_ROOM_NAME
            if room_name != GLOBAL_ROOM_NAME:
                assert rooms.rooms[1].room_name == room_name
            yield ws
        except ValidationError as e:
            assert e == None

def test_ws_connect_sequence(client):
    with ws_for(client, "test_user") as ws:
        pass

def send_room_create(ws: WebSocketTestSession, creator: str, roomname: str):
    room_create = WsRoomCreate(room=RoomInfo(room_name=roomname, room_creator=creator, connected_users=[creator]))
    ws.send_text(room_create.model_dump_json())
    try:
        room_create_response = WsRoomCreate.model_validate_json(ws.receive_text())
        assert room_create == room_create_response
    except ValidationError as e:
        assert e == None


def send_room_create_with_fail(ws: WebSocketTestSession, creator: str, roomname: str):
    room_create = WsRoomCreate(room=RoomInfo(room_name=roomname, room_creator=creator, connected_users=[creator]))
    ws.send_text(room_create.model_dump_json())
    room_create_response = WsRoomCreateReject.model_validate_json(ws.receive_text())
    assert "Room name contains invalid characters" in room_create_response.response


def receive_on_join_messages(ws: WebSocketTestSession):
    try:
        history = WsMessageHistory.model_validate_json(ws.receive_text())
        online_users = WsUsersOnline.model_validate_json(ws.receive_text())
        user_join = WsUserJoinEvent.model_validate_json(ws.receive_text())
    except Exception as e:
        print(f"Error receiving message: {e}")
        assert e == None

def receive_room_switch_msgs(ws: WebSocketTestSession, roomname: str):
    try:
        room_switch_response = WsRoomSwitchResponse.model_validate_json(ws.receive_text())
        assert room_switch_response.room_name == roomname
        history = WsMessageHistory.model_validate_json(ws.receive_text())
        online_users = WsUsersOnline.model_validate_json(ws.receive_text())
    except Exception as e:
        print(f"Error receiving message: {e}")
        assert e == None

def receive_room_switch_reject(ws: WebSocketTestSession, response: str):
    try:
        room_switch_reject = WsRoomSwitchReject.model_validate_json(ws.receive_text())
        assert room_switch_reject.response == response
    except Exception as e:
        print(f"Error receiving message: {e}")
        assert e == None

def test_ws_broadcast_to_all(client):
    users = ["user1", "user2", "user3"]

    def _ws_for(username: str):
        # local wrapper to use the ws_for contextmanager with ExitStack
        return ws_for(client, username)

    with ExitStack() as stack:
        sockets = [stack.enter_context(_ws_for(u)) for u in users]

        for ws in sockets:
            receive_on_join_messages(ws)

        payload_user1 = WsMessage(username=users[0], message="hello all")
        sockets[0].send_text(payload_user1.model_dump_json())

        payload_user2 = WsMessage(username=users[1], message="a second hello")
        sockets[1].send_text(payload_user2.model_dump_json())

        expected_payloads = [payload_user1, payload_user2]

        for ws in sockets:
            while True:
                try:
                    user_msg = TypeAdapter(WsEvent).validate_json(ws.receive_text())
                    if isinstance(user_msg, WsMessage):
                        assert user_msg in expected_payloads
                    if isinstance(user_msg, WsUserJoinEvent):
                        assert user_msg.username in users
                        continue
                    else:
                        break
                except Exception as e:
                    assert e == None

def test_ws_room_create(client):
    room_name = "new_room_name"
    user = "test_user"
    with ws_for(client, user) as ws:
        receive_on_join_messages(ws)
        send_room_create(ws, user, room_name)

def test_ws_room_create_invalid_name(client):
    # A semicolon is not a valid character in a room name
    room_name = ";new_room_name"
    user = "test_user"
    with ws_for(client, user) as ws:
        receive_on_join_messages(ws)
        send_room_create_with_fail(ws, user, room_name)

def test_ws_switch_room(client):
    room_name = "ws_switch_room"
    user = "test_user"
    with ws_for(client, user) as ws:
        receive_on_join_messages(ws)
        send_room_create(ws, user, room_name)
        ws.send_text(WsRoomSwitchRequest(room_name=room_name).model_dump_json())
        receive_room_switch_msgs(ws, room_name)

def test_ws_switch_room_does_not_exist(client):
    # A semicolon is not a valid character in a room name
    room_name = "room_does_not_exist"
    user = "test_user123"
    with ws_for(client, user) as ws:
        receive_on_join_messages(ws)
        ws.send_text(WsRoomSwitchRequest(room_name=room_name).model_dump_json())
        receive_room_switch_reject(ws, f"Room {room_name} not found")

def test_ws_join_new_room(client):
    room_name = "new_room_1"
    user = "test_user1234"
    with ws_for(client, user, room_name) as ws:
        pass
