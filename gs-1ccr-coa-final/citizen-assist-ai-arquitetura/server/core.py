"""Lógica de domínio. Histórico inicial de demonstração é SIMULADO."""
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import threading
import uuid

LOCK = threading.RLock()
DEFAULT_SERVICE_MINUTES = 5.0

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def connect(path):
    db = sqlite3.connect(str(path), check_same_thread=False, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('''CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY, kind TEXT NOT NULL, source TEXT NOT NULL,
        occurred_at TEXT NOT NULL, duration_minutes REAL)''')
    db.commit()
    return db

def training_data():
    """Amostras SINTÉTICAS, criadas só para demonstrar regressão linear."""
    rows = []
    for q in range(1, 13):
        for avg in [3., 4., 5., 6., 7.]:
            # Relação hipotética: ganho por paralelismo e custo fixo de organização.
            target = 0.82 * q * avg + 0.45 * q + 0.7 + ((q * int(avg)) % 3 - 1) * 0.22
            rows.append(([1., float(q), q * avg], target))
    return rows

def fit_regression(samples):
    """Mínimos quadrados com leve regularização; solução Gauss-Jordan 3x3."""
    n = 3
    a = [[sum(x[i]*x[j] for x, _ in samples) + (0.0001 if i == j else 0) for j in range(n)]
         + [sum(x[i]*y for x, y in samples)] for i in range(n)]
    for i in range(n):
        p = max(range(i,n), key=lambda k: abs(a[k][i]))
        a[i],a[p] = a[p],a[i]
        pivot = a[i][i]
        if abs(pivot) < 1e-12: raise ValueError('Matriz singular')
        a[i] = [v/pivot for v in a[i]]
        for k in range(n):
            if k != i:
                factor = a[k][i]
                a[k] = [v - factor*w for v,w in zip(a[k],a[i])]
    return [r[-1] for r in a]

COEFFICIENTS = fit_regression(training_data())

def wait_predictions(queue, mean_minutes):
    if queue == 0: return {'conventional': 0., 'ai': 0.}
    y = COEFFICIENTS[0] + COEFFICIENTS[1]*queue + COEFFICIENTS[2]*queue*mean_minutes
    return {'conventional': round(queue*mean_minutes,1), 'ai': round(max(0,y),1)}

class QueueStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = connect(self.path)
    def close(self): self.db.close()
    def events(self):
        return [dict(r) for r in self.db.execute('SELECT * FROM events ORDER BY rowid').fetchall()]
    def status(self):
        with LOCK:
            ev = self.events()
            arrived = sum(e['kind']=='arrival' for e in ev)
            done = sum(e['kind']=='complete' for e in ev)
            n = arrived-done
            samples = [e['duration_minutes'] for e in ev if e['kind']=='complete' and e['duration_minutes'] and e['duration_minutes']>0]
            avg = round(sum(samples)/len(samples),2) if samples else DEFAULT_SERVICE_MINUTES
            return {'queue':n,'completed':done,'arrivals':arrived,'mean_service_minutes':avg,
                'waiting_minutes':wait_predictions(n,avg),'historical_count':len(samples),
                'training_data':'synthetic', 'device_online':False, 'last_update':ev[-1]['occurred_at'] if ev else None,
                'events':list(reversed(ev[-15:]))}
    def apply(self, kind, source='dashboard', event_id=None, duration_minutes=None):
        if kind not in ('arrival','complete'): raise ValueError('Ação inválida')
        if duration_minutes is not None and (not isinstance(duration_minutes,(int,float)) or duration_minutes<=0 or duration_minutes>240):
            raise ValueError('Duração deve ficar entre 0 e 240 minutos')
        with LOCK:
            event_id = event_id or str(uuid.uuid4())
            existing = self.db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
            if existing: return {'duplicate':True, 'status': self.status()}
            if kind == 'complete' and self.status()['queue']==0: raise ValueError('FILA VAZIA: nenhuma pessoa aguardando')
            self.db.execute('INSERT INTO events(id,kind,source,occurred_at,duration_minutes) VALUES (?,?,?,?,?)',
                            (event_id,kind,source,utc_now(),duration_minutes if kind=='complete' else None))
            self.db.commit()
            return {'duplicate':False,'status':self.status()}
    def reset(self):
        with LOCK:
            self.db.execute('DELETE FROM events')
            self.db.commit()
