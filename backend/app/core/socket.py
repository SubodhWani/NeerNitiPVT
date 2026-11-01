import socketio

# Initialize Socket.IO Async Server for real-time telemetry alerts
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)

@sio.event
async def connect(sid, environ):
    print(f"Socket.IO client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Socket.IO client disconnected: {sid}")

# Helper function to broadcast alerts across connected clients
async def broadcast_alert(title: str, message: str):
    await sio.emit("structure_alert", {"title": title, "message": message})
