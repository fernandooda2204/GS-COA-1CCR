"""API HTTP e ponte MQTT. Uso educacional; não disponibilizar na Internet pública."""
import json
import os
import time
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from .core import QueueStore

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv('CITIZEN_DB', str(ROOT / 'server' / 'data' / 'events.db')))
store = QueueStore(DB_PATH)
MQTT_BROKER = os.getenv('MQTT_BROKER','broker.hivemq.com')
MQTT_TOPIC = os.getenv('MQTT_TOPIC','citizen-assist-ai/fiap-1cc-fev-demo-2026')
last_seen = 0.0
mqtt_state = {'connected':False,'error':None}
client = None
DEVICE_TIMEOUT_S = 35

def device_online():
    return last_seen > 0 and time.monotonic() - last_seen < DEVICE_TIMEOUT_S

def publish_state(status=None):
    """Envia ao ESP32 o estado oficial da fila (servidor), qualquer que seja a origem do evento."""
    if client is None or not mqtt_state['connected']: return
    status = status or store.status()
    client.publish(MQTT_TOPIC+'/state',json.dumps({'queue':status['queue'],'completed':status['completed'],
        'wait':status['waiting_minutes']['ai'],'error':''}),qos=0,retain=False)

def publish_error(message):
    if client is None or not mqtt_state['connected']: return
    client.publish(MQTT_TOPIC+'/state',json.dumps({'error':message}),qos=0,retain=False)

def handle_mqtt(_client, _userdata, msg):
    global last_seen
    try:
        event = json.loads(msg.payload.decode('utf-8'))
        if not isinstance(event,dict): return
        kind = event.get('type')
        if kind == 'heartbeat':
            was_offline = not device_online()
            last_seen = time.monotonic()
            # Dispositivo (re)conectado: sincroniza o display com o estado atual do servidor.
            if was_offline: publish_state()
            return
        if kind not in ('arrival','complete'): return
        last_seen = time.monotonic()
        res = store.apply(kind,source='esp32',event_id=str(event.get('event_id') or '' ) or None)
        publish_state(res['status'])
    except ValueError as exc:
        publish_error(str(exc))
    except Exception as exc:
        mqtt_state['error'] = str(exc)

def start_mqtt():
    global client
    try:
        import paho.mqtt.client as mqtt
        client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_message=handle_mqtt
        def connected(c, _userdata, _flags, reason_code, _properties):
            mqtt_state['connected']=not reason_code.is_failure
            if mqtt_state['connected']:
                c.subscribe(MQTT_TOPIC+'/events')
                publish_state()
        def disconnected(_c,_u,_flags,_rc,_props): mqtt_state['connected']=False
        client.on_connect=connected
        client.on_disconnect=disconnected
        client.connect_async(MQTT_BROKER,1883,60)
        client.loop_start()
    except Exception as exc:
        mqtt_state['error']=str(exc)

@asynccontextmanager
async def lifespan(app):
    if os.getenv('DISABLE_MQTT')!='1': start_mqtt()
    yield
    if client: client.loop_stop()

app=FastAPI(title='Citizen Assist AI', lifespan=lifespan)
app.mount('/static',StaticFiles(directory=str(ROOT/'web')),name='static')

class EventRequest(BaseModel):
    kind: str
    event_id: str | None = Field(default=None,max_length=120)
    duration_minutes: float | None = None

@app.get('/')
def index(): return FileResponse(ROOT/'web'/'index.html')

@app.get('/api/status')
def status():
    v=store.status()
    v['device_online']=device_online()
    v['mqtt_connected']=mqtt_state['connected']
    v['mqtt_error']=mqtt_state['error']
    return v

@app.post('/api/event')
def event(data:EventRequest):
    try:
        res = store.apply(data.kind,event_id=data.event_id,duration_minutes=data.duration_minutes)
    except ValueError as e:
        publish_error(str(e))
        raise HTTPException(status_code=400,detail=str(e)) from e
    # Eventos do painel também atualizam o display do ESP32.
    publish_state(res['status'])
    return res

@app.post('/api/reset')
def reset():
    # Uso somente em demonstração local
    store.reset()
    status = store.status()
    publish_state(status)
    return status
