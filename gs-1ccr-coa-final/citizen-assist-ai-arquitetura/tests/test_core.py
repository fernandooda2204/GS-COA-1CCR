import pytest
from server.core import QueueStore, training_data, fit_regression, wait_predictions

@pytest.fixture
def db(tmp_path):
    s=QueueStore(tmp_path/'test.sqlite')
    yield s
    s.close()

def test_initial(db):
    assert db.status()['queue']==0
    assert db.status()['completed']==0

def test_arrivals(db):
    for _ in range(3): db.apply('arrival')
    assert db.status()['queue']==3
    assert db.status()['waiting_minutes']['ai']>0

def test_completions(db):
    for _ in range(3): db.apply('arrival')
    for _ in range(2): db.apply('complete')
    assert db.status()['queue']==1 and db.status()['completed']==2

def test_no_negative(db):
    with pytest.raises(ValueError,match='FILA VAZIA'): db.apply('complete')
    assert db.status()['queue']==0

def test_no_double_count(db):
    db.apply('arrival',event_id='esp-123')
    result=db.apply('arrival',event_id='esp-123')
    assert result['duplicate'] and db.status()['queue']==1

def test_duration_average(db):
    for _ in range(2):db.apply('arrival')
    db.apply('complete',duration_minutes=4)
    db.apply('complete',duration_minutes=6)
    assert db.status()['mean_service_minutes']==5
    assert db.status()['historical_count']==2

def test_invalid_duration(db):
    db.apply('arrival')
    with pytest.raises(ValueError):db.apply('complete',duration_minutes=-1)

def test_invalid_kind(db):
    with pytest.raises(ValueError):db.apply('other')

def test_predictions_zero():
    assert wait_predictions(0,5)=={'conventional':0.,'ai':0.}

def test_predictions_increase():
    assert wait_predictions(5,5)['ai']>wait_predictions(2,5)['ai']

def test_model_trains():
    c=fit_regression(training_data());assert len(c)==3
    assert 0.5<c[2]<1.1

def test_reset(db):
    db.apply('arrival');db.reset();assert db.status()['queue']==0

def test_persistence(tmp_path):
    p=tmp_path/'x.db';s=QueueStore(p);s.apply('arrival');s.close()
    other=QueueStore(p);assert other.status()['queue']==1;other.close()
