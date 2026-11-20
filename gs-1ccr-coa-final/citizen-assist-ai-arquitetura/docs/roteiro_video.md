# Roteiro de demonstração (máximo: 5 minutos)

Duração prevista: cerca de 3:15. Telas: Wokwi (ESP32, display e monitor serial) e painel em http://localhost:8000, lado a lado.

## Antes de gravar

1. Trocar o tópico MQTT por um nome único da equipe (dois tópicos no `sketch.ino` e `$env:MQTT_TOPIC`).
2. Iniciar o servidor dentro de `citizen-assist-ai-arquitetura`.
3. Abrir o painel e clicar em **Zerar demonstração**.
4. Iniciar a simulação no Wokwi e esperar **Dispositivo online** (cerca de 10 s).

## Cenas

| # | Tempo | O que fazer | O que mostrar |
|---|---|---|---|
| 1 | 0:00–0:20 | Mostrar o circuito e o painel | Botões verde/azul, OLED, LEDs, buzzer; fila 0; dispositivo online |
| 2 | 0:20–0:50 | T1: 3× botão verde (2 s entre cliques) | Fila 3, LED verde, espera 15 min (média) e 14,3 min (IA) |
| 3 | 0:50–1:15 | T2: 2× botão azul | Fila 1, concluídos 2, espera 5 e 5,2 min |
| 4 | 1:15–1:50 | T3: 1× azul (fila 0), depois mais 1× azul | FILA VAZIA no display, LED vermelho, buzzer; painel continua em 0 |
| 5 | 1:50–2:20 | T4: 3× verde, parando após cada clique | IA sobe 5,2 → 9,7 → 14,3 min; média 5 → 10 → 15 min |
| 6 | 2:20–2:35 | Rolar até **Registro de eventos** | Horário e origem (ESP32/Wokwi) de cada evento |
| 7 | 2:35–2:55 | Quadro **Comparativo de previsão** | Média histórica × IA; aviso de dados simulados |
| 8 | 2:55–3:15 | No painel: duração 8 e **Concluir atendimento** | Fila 2, média 8 min, convencional 16 min, IA 14,7 min; display do ESP32 também atualiza |

Os valores consideram o banco zerado e a média padrão de 5 min por atendimento até a cena 8.

Não afirmar que os testes foram feitos com cidadãos reais: a chegada de pessoas é simulada pelos botões.
