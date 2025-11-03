/**
 * WebSockets Workshop - Complete Solution
 *
 * This is the instructor's reference implementation.
 * Students should NOT have access to this file during the workshop.
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

// Fill in username and server address here to not get prompted!
globalThis.CONFIG = {
    // A non-empty username is required, the server may reject the connection,
    // if the username is invalid (too long, contains invalid characters, etc.)
    // If the username is empty, the client will prompt the user for a username.
    username: '',
    // Use an empty room_name to join the global/default room, otherwise
    // setting it to a non-empty string will create a new room for you.
    // No extra setup is required for joining/creating a new room.
    room_name: '',
    // Just input server:port, omit http:// or ws://
    backend_server_address: 'localhost:5000',
    // Set to true if you want to use https instead of http, will also use
    // wss instead of ws when true
    use_https: false,
    // Set to true if you want to use the REST API instead of the WebSocket API
    // Note that the REST API is not the main focus, but it is provided for
    // the sake of comparison.
    use_rest: false,
};


// =============================================================================
// GLOBAL STATE
// =============================================================================

globalThis.websocket = null;
globalThis.lastActivity = performance.now();
globalThis.isTyping = false;
globalThis.GLOBAL_ROOM_NAME = "Global";

const WS_EVENT_TYPES = {
    connection_request: 'connection_request',
    connection_response: 'connection_response',
    connection_reject: 'connection_reject',
    message: 'message',
    message_history: 'message_history',
    typing: 'typing',
    system: 'system',
    users_online: 'users_online',
    user_join: 'user_join',
    user_leave: 'user_leave',
    all_rooms: 'all_rooms',
    // NOTE:There is no special response for room_create, the room_create will be sent back to the client on success
    room_create: 'room_create',
    room_create_reject: 'room_create_reject',
    room_chat_clear: 'room_chat_clear',
    room_switch_request: 'room_switch_request',
    room_switch_response: 'room_switch_response',
    room_switch_reject: 'room_switch_reject',
};


// =============================================================================
// ASSIGNMENT 1 SOLUTION: WEBSOCKET CONNECTION
// =============================================================================

function wsConnectUser(serverUrl, username) {
    try {
        // If you've setup the config right, then serverUrl already contains all you need to connect to the server!
        // Try printint it if you want to see it:
        console.log(`Server URL: ${serverUrl}`);
        globalThis.websocket = new WebSocket(`${serverUrl}`);

        globalThis.websocket.addEventListener('error', (e) => {
            console.error('WebSocket error:', e);
        });

        globalThis.websocket.addEventListener('open', () => {
            console.log('WebSocket connection opened');
            globalThis.websocket.send(JSON.stringify({
                event_type: WS_EVENT_TYPES.connection_request,
                username: username,
            }));
        });

        globalThis.websocket.addEventListener('close', () => {
            console.log('WebSocket connection closed');
            globalThis.websocket = null;
        });

        globalThis.websocket.addEventListener('message', (msg) => {
            const message = JSON.parse(msg.data);
            wsReceiveMessage(message, username);
        });

    } catch (error) {
        console.error('Error connecting user:', error);
        throw error;
    }
}


// =============================================================================
// ASSIGNMENT 2 SOLUTION: SEND AND RECEIVE MESSAGES
// =============================================================================

// This function is invoked by the UI code when you send a message (i.e. press enter or click send)
function wsSendMessage(websocket, message, username) {
    if (!websocket) {
        console.error('WebSocket is not connected');
        return;
    }

    websocket.send(JSON.stringify({
        event_type: WS_EVENT_TYPES.message,
        username: username,
        message: message,
    }));
}

// NOTE: username is your username
// And message is the message that you've just received
function wsReceiveMessage(message, username) {
    console.log('Received message:' + message);

    switch (message.event_type) {
        case WS_EVENT_TYPES.message:
            const own = message.username === username ? "own" : "other";
            if (own === "other") {
                window.addMessageToUI(message.message, own, message.username);
            }
            break;
        case WS_EVENT_TYPES.message_history:
            message.messages.forEach((msg) => {
                console.log(`message ${msg.message}, ${msg}`);
                const own = msg.username === username ? "own" : "other";
                window.addMessageToUI(msg.message, own, msg.username);
            });
            break;

        case WS_EVENT_TYPES.connection_reject:
            createToastForSeverity(message.response, 'error');
            break;

        // ASSIGNMENT 3: User presence notifications
        case WS_EVENT_TYPES.users_online:
            window.addSelfAsOnline();
            message.users.forEach((user) => {
                if (user.username !== username) {
                    window.addMemberToList(user.username, user.status);
                }
            });
            window.updateOnlineCount();
            break;
        case WS_EVENT_TYPES.user_join:
            if (message.username === window.chatConfig.username) {
                return;
            }
            Toast.info(`User ${message.username} joined the chat`);
            window.addMemberToList(message.username, 'online');
            window.updateOnlineCount();
            break;
        case WS_EVENT_TYPES.user_leave:
            if (message.username === window.chatConfig.username) {
                return;
            }
            Toast.info(`User ${message.username} left the chat`);
            window.removeMemberFromList(message.username);
            window.updateOnlineCount();
            break;
        case WS_EVENT_TYPES.system:
            createToastForSeverity(message.message, message.severity);
            break;

        // ASSIGNMENT 4: Typing indicators
        case WS_EVENT_TYPES.typing:
            updateMemberStatus(message.username, message.is_typing ? 'typing' : 'online');
            break;

        // ASSIGNMENT 5: Room management
        case WS_EVENT_TYPES.all_rooms:
            console.log(`rooms: ${message.rooms}`)
            message.rooms.forEach((room) => {
                if (room.room_name == "Global") {
                    return;
                }
                console.log(`Room ${room.room_name} created by ${room.room_creator}`);
                window.addRoomToList(room.room_name, false);
            })
            break;
        case WS_EVENT_TYPES.room_create:
            if (message.room.room_name == "Global") {
                return;
            }
            window.addRoomToList(message.room.room_name, false);
            Toast.success(`Room ${message.room.room_name} created by ${message.room.room_creator}`);
            break;
        case WS_EVENT_TYPES.room_create_reject:
            createToastForSeverity(message.response, 'error');
            break;
        case WS_EVENT_TYPES.room_switch_response:
            if (message.room_name === window.chatConfig.room_name) {
                return;
            }
            console.log(`Room switched to ${message.room_name}`);
            window.switchToRoom(message.room_name);
            break;
        case WS_EVENT_TYPES.room_switch_reject:
            createToastForSeverity(message.response, 'error');
            break;
        case WS_EVENT_TYPES.room_chat_clear:
            window.clearChat(message.room_name);
            break;

        default:
            console.log('Received unknown message:' + JSON.stringify(message));
    }
}


// =============================================================================
// ASSIGNMENT 4 SOLUTION: TYPING INDICATORS
// =============================================================================

window.addEventListener('keydown', (_event) => {
    if (!globalThis.websocket) {
        return;
    }

    if (!globalThis.isTyping) {
        globalThis.isTyping = true;
        globalThis.lastActivity = performance.now();

        const isTypingMessage = {
            event_type: WS_EVENT_TYPES.typing,
            username: window.chatConfig.username,
            is_typing: true,
        };
        globalThis.websocket.send(JSON.stringify(isTypingMessage));
    }
});

window.setInterval(() => {
    if (!globalThis.websocket) { return }

    if (!globalThis.isTyping) {
        return;
    }

    if ((performance.now() - globalThis.lastActivity) > 2500) {
        globalThis.isTyping = false;
        const isTypingMessage = {
            event_type: WS_EVENT_TYPES.typing,
            username: window.chatConfig.username,
            is_typing: false,
        };
        globalThis.websocket.send(JSON.stringify(isTypingMessage));
    }
}, 500);


// =============================================================================
// ASSIGNMENT 5 SOLUTION: ROOM MANAGEMENT
// =============================================================================

function wsSendRoomCreate(websocket, roomName) {
    websocket.send(JSON.stringify(
        {
            event_type: WS_EVENT_TYPES.room_create,
            room: {
                room_name: roomName,
                room_creator: window.chatConfig.username,
                connected_users: [],
            }
        }
    ))
}

function wsSendRoomSwitchReq(websocket, roomName) {
    websocket.send(JSON.stringify({
        event_type: WS_EVENT_TYPES.room_switch_request,
        room_name: roomName,
    }));
}

function wsSendRoomChatClear(websocket, roomName) {
    websocket.send(JSON.stringify({
        event_type: WS_EVENT_TYPES.room_chat_clear,
        room_name: roomName,
        username: window.chatConfig.username,
    }));
}


// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function createToastForSeverity(message, severity) {
    switch (severity) {
        case 'success':
            Toast.success(message);
            break;
        case 'info':
            Toast.info(message);
            break;
        case 'warning':
            Toast.warning(message);
            break;
        case 'error':
            Toast.error(message);
            break;
    }
}


// =============================================================================
// EXPORTS
// =============================================================================

window.wsSendRoomCreate = wsSendRoomCreate;
window.wsSendRoomSwitchReq = wsSendRoomSwitchReq;
window.wsSendRoomChatClear = wsSendRoomChatClear;
