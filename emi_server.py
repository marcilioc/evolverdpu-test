import socketio
import serial
import evolver
import time
import asyncio
import json
import sys
import os
import yaml
# import redis
import time
from traceback import print_exc

LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
IMMEDIATE = 'immediate_command_char'
RECURRING = 'recurring_command_char'
CALIBRATIONS_FILENAME = 'calibrations.json'
CONF_FILENAME = 'conf.yml'
evolver_conf = {}
command_queue = []

with open(os.path.realpath(os.path.join(os.getcwd(),os.path.dirname(__file__), CONF_FILENAME)), 'r') as ymlfile:
        evolver_conf = yaml.load(ymlfile, Loader=yaml.FullLoader)

# redis_client = redis.Redis("127.0.0.1")

async def background_task():
    while(broadcast_enable):
        print("Broadcast")
        # data = json.loads(redis_client.get("broadcast"))
        data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        await sio.emit('broadcast', data, namespace = '/dpu-evolver')
        time.sleep(25)

# Create socket.IO Server
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio)
background_task_started = False
broadcast_enable = False

@sio.on('connect', namespace = '/dpu-evolver')
async def connect(sid, environ, namespace = '/dpu-evolver'):
    print('connected as a server')

@sio.event
async def disconnect(sid, environ, namespace = '/dpu-evolver'):
    print('disconnected from client')
    global broadcast_enable
    broadcast_enable = False

@sio.on('getdevicename', namespace = '/dpu-evolver')
async def on_getdevicename(sid, data):
    print("Getdevicename")
    with open('test_device.json') as f:
       configJSON = json.load(f)
    print(configJSON)
    await sio.emit('broadcastname', configJSON, namespace = '/dpu-evolver')
    # global background_task_started, broadcast_enable
    # if not background_task_started:
    #     broadcast_enable = True
    #     sio.start_background_task(background_task)
    #     background_task_started = True

@sio.on('command', namespace = '/dpu-evolver')
async def on_command(sid, data):
    print('Received COMMAND', flush = True)
    command = {"payload": data, "reply": True, "command": "command"}
    redis_client.lpush("socketio", json.dumps(command))
    print(command)
    await sio.emit('commandbroadcast', data, namespace = '/dpu-evolver')
    print('commandbroadcast sent')

@sio.on('getactivecal', namespace = '/dpu-evolver')
async def on_getactivecal(sid, data):
    print('Received getactivecal', flush = True)
    redis_client.lpush("socketio", json.dumps({"command": "getactivecal"}))
    ans = redis_client.brpop("socketio_ans")
    ans = json.loads(ans[1].decode('UTF-8', errors='ignore').lower())
    print(ans)
    await sio.emit('activecalibrations', ans, namespace = '/dpu-evolver')

@sio.on('setrawcalibration', namespace = '/dpu-evolver')
async def on_setrawcalibration(sid, data):
    print('setrawcalibration', data, flush = True)
    command = {"payload": data, "command": "setrawcalibration"}
    redis_client.lpush("socketio", json.dumps(command))
    ans = redis_client.brpop("socketio_ans")
    ans = ans[1].decode('UTF-8', errors='ignore')
    print(ans)
    await sio.emit('calibrationrawcallback', ans, namespace = '/dpu-evolver')

@sio.on('startcalibration', namespace = '/dpu-evolver')
async def on_startcalibration(sid, data):
    print('startcalibration', data, flush = True)
    # CALIBRAR COM O SCRIPT!
    # data deve informar o tipo de cal
    await sio.emit('calibrationfinished', 'nomedacalibracao', namespace = '/dpu-evolver')

@sio.on('getcalibration', namespace = '/dpu-evolver')
async def on_getcalibration(sid, data):
    with open(os.path.join(LOCATION, CALIBRATIONS_FILENAME)) as f:
        calibrations = json.load(f)
        for calibration in calibrations:
            if calibration["name"] == data["name"]:
                await sio.emit('calibration', calibration, namespace = '/dpu-evolver')
                break