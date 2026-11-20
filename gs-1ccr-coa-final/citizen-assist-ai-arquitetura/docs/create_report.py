"""Gera docs/relatorio_tecnico.pdf.

Uso (dentro de citizen-assist-ai-arquitetura):  python docs/create_report.py
Preencha INTEGRANTES e VIDEO_URL abaixo antes de gerar a versão final.
O script roda os testes automatizados e escreve o resultado real no relatório.
"""
from datetime import date
from pathlib import Path
import os
import subprocess
import sys

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------- preencher
INTEGRANTES = [
    ('_____________________________________', '______________'),
    ('_____________________________________', '______________'),
]
REPO_URL = 'https://github.com/fernandooda2204/GS-1CCR-COA'
VIDEO_URL = 'PENDENTE DE PREENCHIMENTO'
# --------------------------------------------------------------------------

DOCS = Path(__file__).resolve().parent
ROOT = DOCS.parent
OUT = DOCS / 'relatorio_tecnico.pdf'
DIAGRAM = DOCS / 'diagrama_arquitetura.png'

def register_fonts():
    """Usa DejaVu (Linux), Arial (Windows) ou Arial (macOS); se nenhuma existir, Helvetica."""
    candidates = [
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        (r'C:\Windows\Fonts\arial.ttf', r'C:\Windows\Fonts\arialbd.ttf'),
        ('/Library/Fonts/Arial.ttf', '/Library/Fonts/Arial Bold.ttf'),
        ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont('Body', regular))
            pdfmetrics.registerFont(TTFont('Body-Bold', bold))
            pdfmetrics.registerFontFamily('Body', normal='Body', bold='Body-Bold', italic='Body', boldItalic='Body-Bold')
            return 'Body', 'Body-Bold'
    return 'Helvetica', 'Helvetica-Bold'

def run_tests():
    """Executa o pytest e devolve (linha de resumo, sucesso) ou None se pulado."""
    if os.getenv('REPORT_SKIP_PYTEST') == '1':
        return None
    try:
        r = subprocess.run([sys.executable, '-m', 'pytest', '-q'], cwd=ROOT, capture_output=True, text=True, timeout=300)
    except Exception as exc:
        return f'não foi possível executar: {exc}', False
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    return (lines[-1] if lines else 'sem saída'), r.returncode == 0

FONT, FONT_BOLD = register_fonts()
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='MainTitleX', fontName=FONT_BOLD, fontSize=23, leading=31, textColor=colors.HexColor('#18233b'), spaceAfter=16))
styles.add(ParagraphStyle(name='SubX', fontName=FONT_BOLD, fontSize=12, leading=18, textColor=colors.HexColor('#df006c'), spaceBefore=16, spaceAfter=8))
styles.add(ParagraphStyle(name='Sub2X', fontName=FONT_BOLD, fontSize=10, leading=15, textColor=colors.HexColor('#18233b'), spaceBefore=10, spaceAfter=5))
styles.add(ParagraphStyle(name='BodyX', fontName=FONT, fontSize=9.4, leading=14.5, spaceAfter=6))
styles.add(ParagraphStyle(name='SmallX', fontName=FONT, fontSize=8.2, leading=11.5))
styles.add(ParagraphStyle(name='SmallBoldX', fontName=FONT_BOLD, fontSize=8.2, leading=11.5))
styles.add(ParagraphStyle(name='CaptionX', fontName=FONT, fontSize=8, leading=12, alignment=TA_CENTER, textColor=colors.HexColor('#64748b')))
P = lambda s, style='BodyX': Paragraph(s, styles[style])
story = []
def heading(s): story.append(P(s, 'SubX'))
def subheading(s): story.append(P(s, 'Sub2X'))
def body(s): story.append(P(s))
def bullets(items):
    for it in items: story.append(P('• ' + it))
def table(data, widths):
    rows = [[P(str(x), 'SmallBoldX' if i == 0 else 'SmallX') for x in row] for i, row in enumerate(data)]
    t = Table(rows, colWidths=widths, hAlign='LEFT', repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fce6f0')),
        ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#e5e7eb')), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(t)
    story.append(Spacer(1, .25*cm))

tests = run_tests()
today = date.today().strftime('%d/%m/%Y')

# ------------------------------------------------------------------ capa
story.extend([Spacer(1, .6*cm), P('GLOBAL SOLUTION 2026.2  |  FIAP', 'SubX'), P('Citizen Assist AI', 'MainTitleX'),
              P('Sistema inteligente de gerenciamento de filas virtuais', 'SubX'), Spacer(1, .3*cm)])
body('<b>Disciplina:</b> Computer Organization and Architecture / Arquitetura e Organização de Computadores')
body('<b>Turma:</b> 1CC-FEV &nbsp;&nbsp; <b>Modalidade:</b> protótipo funcional + relatório técnico')
for i, (nome, rm) in enumerate(INTEGRANTES, 1):
    body(f'<b>Integrante {i}:</b> {nome} &nbsp;&nbsp; <b>RM:</b> {rm}')
body(f'<b>Repositório:</b> {REPO_URL}')
body(f'<b>Vídeo:</b> {VIDEO_URL}')

heading('Resumo executivo')
body('Foi desenvolvido um protótipo acadêmico de fila virtual. Um ESP32 simulado no Wokwi lê dois botões '
     '(chegada e conclusão) e envia cada evento por Wi-Fi e MQTT a um servidor Python. O servidor guarda os eventos '
     'com horário em SQLite, impede contagens negativas e eventos duplicados, calcula o tempo de espera por média '
     'histórica e por regressão linear, e devolve o estado ao ESP32, que atualiza display OLED, LEDs e buzzer. '
     'Um painel web mostra a fila, a espera estimada e os atendimentos concluídos. A regressão linear foi treinada '
     'com dados <b>sintéticos</b>, identificados como tal.')

heading('Estado de verificação')
if tests is None:
    test_line = 'Resultado dos testes automatizados: gere o relatório novamente com <b>python docs/create_report.py</b> para incluir a execução.'
else:
    summary, ok = tests
    color = '#137a50' if ok else '#b91c1c'
    test_line = f'Testes automatizados executados em {today} com <b>python -m pytest -q</b>: <font color="{color}">{summary}</font>.'
body(test_line + ' São 13 testes de domínio (fila, persistência, deduplicação, validação, previsão) e 2 da API HTTP, '
     'que usam banco temporário.')
body('<b>Pendente:</b> registrar as capturas do teste ponta a ponta no Wokwi (ESP32 + broker MQTT) e o vídeo. '
     'O teste visual no Wokwi só deve ser declarado como comprovado depois de executado.')

# ------------------------------------------------------- 1. arquitetura
story.append(PageBreak())
heading('1. Arquitetura computacional')
body('O sistema tem dois nós de processamento: o ESP32, na borda, cuida da entrada e da saída física; o computador '
     'executa a API, guarda o histórico e calcula as previsões. Os dois se comunicam por um broker MQTT na internet, '
     'e o navegador acessa a API por HTTP.')
if DIAGRAM.exists():
    w = 17.2*cm
    story.append(Image(str(DIAGRAM), width=w, height=w*600/1000))
story.append(P('Figura 1 - Componentes, conexões e fluxo de informações do protótipo (elaboração própria; '
               'arquivo docs/diagrama_arquitetura.svg).', 'CaptionX'))

heading('2. Funções dos componentes')
table([
    ['Componente', 'Onde', 'Papel no sistema'],
    ['CPU', 'ESP32 / computador', 'O ESP32 lê os botões, monta e envia mensagens, recebe o estado e controla os periféricos. A CPU do computador executa a API, as regras da fila e a regressão linear.'],
    ['Memória RAM', 'SRAM do ESP32 / RAM do PC', 'Variáveis da fila, buffers das mensagens JSON e MQTT, framebuffer do display; no PC, o processo Python e o cache do SQLite.'],
    ['Armazenamento', 'Flash do ESP32 / disco do PC', 'A flash guarda o firmware; o disco guarda o banco SQLite com todos os eventos e horários.'],
    ['Entrada', 'Botões / painel web', 'Botão CHEGADA (GPIO 18) e CONCLUSÃO (GPIO 19); botões virtuais do painel.'],
    ['Saída', 'OLED, LEDs, buzzer / painel', 'Display com fila, concluídos e espera; LED verde (há fila), LED vermelho e buzzer (operação inválida); painel web.'],
    ['Comunicação', 'Wi-Fi, MQTT, HTTP', 'Wi-Fi + MQTT entre ESP32 e servidor; HTTP/JSON entre navegador e API.'],
], [3*cm, 3.6*cm, 10.6*cm])

# ------------------------------------------------------- 3. fila
heading('3. Implementação da fila virtual')
body('Cada clique gera um evento <i>arrival</i> ou <i>complete</i> com identificador único (event_id). A API grava o '
     'evento no SQLite com origem (ESP32 ou painel) e horário UTC. A fila é calculada como chegadas menos conclusões. '
     'Uma conclusão com a fila vazia é rejeitada com a mensagem FILA VAZIA e nada é gravado, então a contagem nunca '
     'fica negativa. Um event_id repetido (reenvio de mensagem) é ignorado.')
body('O estado oficial fica no servidor. A cada evento aceito, venha ele do ESP32 ou do painel, a API publica o estado '
     'no tópico MQTT .../state, e o ESP32 atualiza display, LEDs e buzzer. Quando o ESP32 volta a ficar online, o '
     'servidor envia o estado atual para sincronizar o display. O painel web consulta GET /api/status a cada 2 segundos.')

# ------------------------------------------------------- 4. previsão
heading('4. Previsão inteligente de espera')
body('<b>Método convencional:</b> T = N × M, em que N é o número de pessoas aguardando e M é a média histórica da '
     'duração dos atendimentos, em minutos. Sem durações registradas, o sistema usa 5 minutos. A duração de um '
     'atendimento é informada no painel ao concluí-lo e passa a compor a média histórica.')
body('<b>Regressão linear:</b> T = b0 + b1 × N + b2 × (N × M). Os coeficientes são ajustados por mínimos quadrados '
     '(sistema 3×3 resolvido por Gauss-Jordan, com pequena regularização). Um piso de zero impede espera negativa.')
body('<b>Origem dos dados:</b> o treinamento usa 60 amostras <b>sintéticas</b> (filas de 1 a 12 pessoas e médias de '
     '3 a 7 minutos), geradas a partir de um cenário hipotético com pequeno ganho de eficiência em filas maiores. '
     'Não são dados de cidadãos ou de serviços reais. Por isso a previsão é ilustrativa.')
table([
    ['Pessoas na fila (M = 5 min)', '1', '2', '3', '4', '5', '10'],
    ['Convencional (min)', '5,0', '10,0', '15,0', '20,0', '25,0', '50,0'],
    ['Regressão linear (min)', '5,2', '9,7', '14,3', '18,8', '23,4', '46,1'],
], [5.2*cm] + [2*cm]*6)
body('Com M = 8 min e 2 pessoas, a estimativa convencional é 16,0 min e a da regressão, 14,7 min.')

# ------------------------------------------------------- 5. análise
story.append(PageBreak())
heading('5. Análise da arquitetura computacional')
subheading('5.1 Processador')
body('O ESP32 (módulo ESP32-WROOM-32 na placa DevKit V1) tem CPU Xtensa LX6 de 32 bits com dois núcleos de até '
     '240 MHz, barramentos separados para instruções e dados, e Wi-Fi 802.11 b/g/n e Bluetooth integrados. '
     'Na plataforma Arduino-ESP32, o FreeRTOS executa a pilha Wi-Fi e TCP/IP principalmente no núcleo 0, e a função '
     'loop() do firmware no núcleo 1. Assim, a leitura dos botões e o desenho no display não disputam o mesmo núcleo '
     'com o rádio.')
body('No servidor, a CPU x86-64 do computador executa o interpretador Python, o FastAPI, o cliente MQTT e o SQLite. '
     'A regressão é treinada uma única vez, na inicialização; cada previsão custa poucas multiplicações.')

subheading('5.2 Organização da memória e estimativa de utilização')
body('O ESP32 tem 448 KB de ROM (bootloader e rotinas internas), 520 KB de SRAM interna para dados e código rápido, '
     '16 KB de SRAM no domínio RTC e, na placa, 4 MB de flash externa ligada por SPI. O firmware é gravado na flash e '
     'executado por meio de cache. No esquema de partições padrão do Arduino, cerca de 1,2 MB da flash ficam para o '
     'programa.')
table([
    ['Item na RAM do ESP32', 'Tamanho estimado', 'Observação'],
    ['Variáveis da fila (fila, concluídos, espera, tempos, sequência)', 'cerca de 30 bytes', 'int, float, bool, unsigned long (variáveis globais)'],
    ['Framebuffer do OLED 128×64', '1.024 bytes', '128 × 64 pixels ÷ 8 bits; alocado pela biblioteca SSD1306'],
    ['Buffer do PubSubClient', '256 bytes', 'tamanho padrão do pacote MQTT'],
    ['JSON recebido (StaticJsonDocument)', '256 bytes', 'na pilha, só durante o callback'],
    ['JSON enviado + texto serializado', '384 bytes', 'na pilha, só durante o envio'],
    ['Total da aplicação', 'menos de 2 KB', 'menos de 0,5% dos 520 KB de SRAM'],
    ['Pilhas Wi-Fi, TCP/IP e FreeRTOS', 'dezenas de KB', 'maior consumo de RAM; medir com ESP.getFreeHeap()'],
], [6.4*cm, 3.3*cm, 7.5*cm])
body('Os valores exatos de flash e RAM do firmware aparecem na saída de compilação (linhas "Sketch uses" e '
     '"Global variables use"). A maior parte do firmware vem das bibliotecas de Wi-Fi e TCP/IP, não da lógica da fila.')
body('No servidor, cada evento ocupa cerca de 100 bytes no SQLite (UUID, tipo, origem, horário). Mil eventos ocupam '
     'cerca de 100 KB, valor desprezível para o disco do computador. O banco usa o modo WAL, que permite leituras '
     'enquanto há escrita.')

subheading('5.3 Operações de entrada, processamento e saída')
table([
    ['Etapa', 'Onde', 'Como funciona'],
    ['Entrada física', 'ESP32', 'Botões com pull-up interno: nível LOW ao pressionar. O loop lê os pinos a cada 20 ms (polling) com debounce de 350 ms.'],
    ['Entrada web', 'Navegador', 'Botões do painel enviam POST /api/event com o tipo do evento e, opcionalmente, a duração.'],
    ['Processamento local', 'ESP32', 'Monta o JSON com event_id (MAC + millis + sequência), publica no MQTT e interpreta o estado recebido.'],
    ['Processamento central', 'Servidor', 'Valida, descarta duplicatas, impede fila negativa, grava no SQLite e calcula as duas previsões.'],
    ['Saída local', 'ESP32', 'OLED por I²C; LED verde quando há fila; LED vermelho e buzzer (tone, PWM) em operação inválida.'],
    ['Saída web', 'Navegador', 'Painel com fila, previsões, concluídos e registro de eventos, atualizado a cada 2 s.'],
], [3.4*cm, 2.4*cm, 11.4*cm])

subheading('5.4 Comunicação entre dispositivos e protocolos')
table([
    ['Protocolo', 'Entre', 'Características'],
    ['GPIO digital', 'ESP32 e botões/LEDs', 'Sinais de 3,3 V; leitura e escrita de nível lógico.'],
    ['I²C', 'ESP32 e display OLED', 'Barramento serial de dois fios (SDA no GPIO 21, SCL no GPIO 22), endereço 0x3C.'],
    ['Wi-Fi (IEEE 802.11 b/g/n)', 'ESP32 e rede', 'Rádio de 2,4 GHz; no Wokwi, rede simulada Wokwi-GUEST.'],
    ['MQTT sobre TCP/IP', 'ESP32, broker e API', 'Publicação/assinatura na porta 1883, QoS 0. Tópicos .../events (eventos e heartbeat a cada 10 s) e .../state (estado da fila).'],
    ['HTTP + JSON', 'Navegador e API', 'API REST: GET /api/status, POST /api/event e POST /api/reset.'],
    ['SQL (SQLite)', 'API e disco', 'Banco em arquivo local, modo WAL.'],
], [4*cm, 3.6*cm, 9.6*cm])

subheading('5.5 Limitações de desempenho, memória e conectividade')
bullets([
    '<b>Desempenho:</b> o painel usa polling de 2 s, então a tela pode atrasar até 2 s. A cada consulta, o servidor '
    'recalcula a fila lendo todos os eventos (custo proporcional ao histórico); com muitos milhares de eventos seria '
    'melhor manter contadores ou consultas agregadas.',
    '<b>Memória:</b> os buffers JSON e MQTT têm tamanho fixo (192 e 256 bytes), suficiente para as mensagens atuais. '
    'O ESP32 não guarda eventos localmente: um clique feito sem conexão com o broker é perdido.',
    '<b>Conectividade:</b> o broker público não tem autenticação nem criptografia e pode ficar indisponível. O QoS 0 não '
    'garante entrega. Enquanto o ESP32 tenta reconectar ao MQTT, o loop fica bloqueado e os botões não são lidos. '
    'O servidor considera o dispositivo offline após 35 s sem mensagens.',
])

# ------------------------------------------------------- 6. testes
heading('6. Testes e resultados')
table([
    ['Teste', 'Ação', 'Resultado esperado', 'Situação'],
    ['T1', '3 chegadas', 'fila = 3; LED verde; espera 15,0 (média) e 14,3 min (IA)', 'Verificado nos testes automatizados; Wokwi: registrar captura'],
    ['T2', '2 conclusões após T1', 'fila = 1; concluídos = 2', 'Verificado nos testes automatizados; Wokwi: registrar captura'],
    ['T3', 'conclusão com fila vazia', 'erro FILA VAZIA, LED vermelho e buzzer; fila nunca negativa', 'Verificado nos testes automatizados; Wokwi: registrar captura'],
    ['T4', 'novas chegadas', 'as duas estimativas aumentam (IA: 5,2, 9,7, 14,3 min)', 'Verificado nos testes automatizados; Wokwi: registrar captura'],
], [1.4*cm, 3.4*cm, 6.4*cm, 6*cm])
body(test_line)

# ------------------------------------------------------- 7. segurança
heading('7. Segurança e próximos passos')
body('O protótipo não tem autenticação e deve rodar só no computador local (127.0.0.1). Não devem ser enviados dados '
     'pessoais pelo broker público, e cada equipe deve usar um tópico MQTT próprio. Próximos passos: broker privado com '
     'TLS e senha, QoS 1, fila local de eventos no ESP32 para quedas de conexão, medição automática da duração dos '
     'atendimentos e retreino do modelo com dados reais autorizados.')

heading('8. Referências e anexos')
body('FIAP. Global Solution 2026.2 - Citizen Assist AI - Computer Organization and Architecture (enunciado). '
     'Espressif Systems. ESP32 Series Datasheet. '
     f'Anexos no repositório ({REPO_URL}): código-fonte, README, testes, firmware e circuito Wokwi, diagrama de '
     'arquitetura e roteiro do vídeo.')

def page(c, doc):
    c.saveState(); w, h = doc.pagesize
    c.setStrokeColor(colors.HexColor('#e50071')); c.setLineWidth(2); c.line(1.7*cm, h-1.2*cm, w-1.7*cm, h-1.2*cm)
    c.setFont(FONT, 8); c.setFillColor(colors.HexColor('#8591a3'))
    c.drawString(1.7*cm, 1.2*cm, 'FIAP 2026.2  |  Citizen Assist AI  |  Relatório técnico')
    c.drawRightString(w-1.7*cm, 1.2*cm, str(doc.page)); c.restoreState()

doc = SimpleDocTemplate(str(OUT), pagesize=(21*cm, 29.7*cm), rightMargin=1.8*cm, leftMargin=1.8*cm,
                        topMargin=1.65*cm, bottomMargin=1.75*cm, title='Citizen Assist AI - Relatório Técnico')
doc.build(story, onFirstPage=page, onLaterPages=page)
print(OUT)
