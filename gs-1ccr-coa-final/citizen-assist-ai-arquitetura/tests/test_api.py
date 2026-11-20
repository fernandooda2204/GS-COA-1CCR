import os
import tempfile
from pathlib import Path

# Banco temporário: os testes nunca apagam os eventos da demonstração (server/data/events.db).
os.environ['DISABLE_MQTT'] = '1'
os.environ['CITIZEN_DB'] = str(Path(tempfile.mkdtemp()) / 'test_events.db')

from fastapi.testclient import TestClient
from server.app import app, DB_PATH

def test_usa_banco_temporario():
    assert DB_PATH.name == 'test_events.db'

def test_http_flow():
    with TestClient(app) as client:
        client.post('/api/reset')
        assert client.get('/api/status').json()['queue']==0
        assert client.post('/api/event',json={'kind':'arrival'}).status_code==200
        assert client.get('/api/status').json()['queue']==1
        assert client.post('/api/event',json={'kind':'complete'}).status_code==200
        assert client.post('/api/event',json={'kind':'complete'}).status_code==400
        assert client.get('/').status_code==200
        client.post('/api/reset')
