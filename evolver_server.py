import socketio
import serial
import evolver
import time
import asyncio
import json
import sys
import os
import yaml
from traceback import print_exc

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

@sio.on('command', namespace = '/dpu-evolver')
async def on_command(sid, data):
    global command_queue, evolver_conf
    print('Received COMMAND', flush = True)
    param = data.get('param', None)
    value = data.get('value', None)
    immediate = data.get('immediate', None)
    recurring = data.get('recurring', None)
    fields_expected_outgoing = data.get('fields_expected_outgoing', None)
    fields_expected_incoming = data.get('fields_expected_incoming', None)

    # Update the configuration for the param
    if value is not None:
        if type(value) is list and evolver_conf['experimental_params'][param]['value'] is not None:
            for i, v in enumerate(value):
                if v != 'NaN':
                    evolver_conf['experimental_params'][param]['value'][i] = value[i]
        else:
            evolver_conf['experimental_params'][param]['value'] = value
    if recurring is not None:
        evolver_conf['experimental_params'][param]['recurring'] = recurring
    if fields_expected_outgoing is not None:
        evolver_conf['experimental_params'][param]['fields_expected_outgoing'] = fields_expected_outgoing
    if fields_expected_incoming is not None:
        evolver_conf['experimental_params'][param]['fields_expected_incoming'] = fields_expected_incoming


    # Save to config the values sent in for the parameter
    with open(os.path.realpath(os.path.join(os.getcwd(),os.path.dirname(__file__), evolver.CONF_FILENAME)), 'w') as ymlfile:
        yaml.dump(evolver_conf, ymlfile)

    if immediate:
        clear_broadcast(param)
        command_queue.insert(0, {'param': param, 'value': value, 'type': IMMEDIATE})
    await sio.emit('commandbroadcast', data, namespace = '/dpu-evolver')
