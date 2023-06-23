import socketio
import os
import json

LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
evolver_conf = {}

# Create socket.IO Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# warp with a WSGI application
app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ, namespace = '/dpu-evolver'):
    print('connected as a server')

@sio.event
async def disconnect(sid, environ, namespace = '/dpu-evolver'):
    print('disconnected from client')

@sio.on('getdevicename', namespace = '/dpu-evolver')
async def on_getdevicename(sid, data):
    config_path = os.path.join(LOCATION)
    with open(os.path.join(LOCATION, 'test_device.json')) as f:
       configJSON = json.load(f)
    await sio.emit('broadcastname', configJSON, namespace = '/dpu-evolver')
