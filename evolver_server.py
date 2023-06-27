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
IMMEDIATE = 'immediate_command_char'
RECURRING = 'recurring_command_char'
CALIBRATIONS_FILENAME = 'calibrations.json'
CONF_FILENAME = 'conf.yml'
evolver_conf = {}
command_queue = []

with open(os.path.realpath(os.path.join(os.getcwd(),os.path.dirname(__file__), CONF_FILENAME)), 'r') as ymlfile:
        evolver_conf = yaml.load(ymlfile, Loader=yaml.FullLoader)

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
    print('commandbroadcast sent')

# Broadcast definitions
def clear_broadcast(param=None):
    """ Removes broadcast commands of a specific param from queue """
    global command_queue
    for i, command in enumerate(command_queue):
        if (command['param'] == param or param is None) and command['type'] == RECURRING:
            command_queue.pop(i)
            break

async def run_commands():
    global command_queue, serial_connection
    data = {}
    while len(command_queue) > 0:
        command = command_queue.pop(0)
        try:
            if command['param'] == 'wait':
                time.sleep(command['value'])
                continue
            returned_data = serial_communication(command['param'], command['value'], command['type'])
            if returned_data is not None:
                data[command['param']] = returned_data
        except (TypeError, ValueError, serial.serialutil.SerialException, EvolverSerialError) as e:
            print_exc(file = sys.stdout)
    return data

def get_num_commands():
    global command_queue
    return len(command_queue)

def process_commands(parameters):
    """
        Add all recurring commands and pre/post commands to the command queue
        Immediate commands will have already been added to queue, so are ignored
    """
    for param, config in parameters.items():
        if config['recurring']: 
            if "pre" in config: # run this command prior to the main command
                sub_command(config['pre'], parameters)

            # Main command
            command_queue.append({'param': param, 'value': config['value'], 'type': RECURRING})

            if "post" in config: # run this command after the main command
                sub_command(config['post'], parameters)

def sub_command(command_list, parameters):
    """
        Append a list of commands to the command queue
    """
    for command in command_list:
        parameter = command['param']
        value = command['value']
        if value == 'values':
            value = parameters[parameter]['value']
        command_queue.append({'param': parameter, 'value': value, 'type': IMMEDIATE})

async def broadcast(commands_in_queue):
    global command_queue
    broadcast_data = {}
    clear_broadcast()
    if not commands_in_queue:
        process_commands(evolver_conf['experimental_params'])

    # Always run commands so that IMMEDIATE requests occur. RECURRING requests only happen if no commands in queue
    broadcast_data['data'] = await run_commands()
    broadcast_data['config'] = evolver_conf['experimental_params']
    if not commands_in_queue:
        print('Broadcasting data', flush = True)
        broadcast_data['ip'] = evolver_conf['evolver_ip']
        broadcast_data['timestamp'] = time.time()
        print(broadcast_data, flush = True)
        await sio.emit('broadcast', broadcast_data, namespace='/dpu-evolver')
