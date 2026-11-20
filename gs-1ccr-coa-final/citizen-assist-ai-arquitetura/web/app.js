const id = x => document.getElementById(x);
async function api(url, method='GET', data) {
 const resp = await fetch(url,{method,headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});
 const payload=await resp.json();if(!resp.ok)throw Error(payload.detail || 'Falha na requisição');return payload;
}
async function refresh(){try{
 const d=await api('/api/status');id('queue').textContent=d.queue;id('completed').textContent=d.completed;
 id('wait-ai').textContent=d.waiting_minutes.ai;id('wait-normal').textContent=d.waiting_minutes.conventional+' min';
 id('wait-ai-row').textContent=d.waiting_minutes.ai+' min';id('average').textContent=d.mean_service_minutes+' min';id('samples').textContent=d.historical_count;
 id('device').textContent=d.device_online?'Dispositivo online':'Dispositivo offline';id('device-dot').classList.toggle('online',d.device_online);
 const events = d.events;id('events').replaceChildren();
 if(!events.length){const tr=document.createElement('tr');const td=document.createElement('td');td.colSpan=3;td.textContent='Nenhum evento registrado.';tr.append(td);id('events').append(tr);}
 for(const e of events){const tr=document.createElement('tr');for(const value of [new Date(e.occurred_at).toLocaleString('pt-BR'),e.kind==='arrival'?'Chegada':'Atendimento concluído',e.source==='esp32'?'ESP32/Wokwi':'Painel web']){const td=document.createElement('td');td.textContent=value;tr.append(td)}id('events').append(tr)}
 }catch(e){id('alert').textContent='Erro ao atualizar: '+e.message}}
async function action(kind){try{const raw=id('duration').value;const duration=kind==='complete'&&raw!==''?Number(raw):null;await api('/api/event','POST',{kind,duration_minutes:duration});id('alert').textContent='';await refresh()}catch(e){id('alert').textContent=e.message}}
id('add').onclick=()=>action('arrival');id('finish').onclick=()=>action('complete');id('reset').onclick=async()=>{if(confirm('Zerar todos os eventos desta demonstração?')){await api('/api/reset','POST');id('alert').textContent='';await refresh()}};
refresh();setInterval(refresh,2000);
