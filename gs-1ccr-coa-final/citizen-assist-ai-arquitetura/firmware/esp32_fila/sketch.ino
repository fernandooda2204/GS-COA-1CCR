// Citizen Assist AI - ESP32 Wokwi. Eventos MQTT; estado oficial no servidor.
#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>

const char* BROKER = "broker.hivemq.com";
// Deve coincidir com MQTT_TOPIC no arquivo .env / terminal do servidor.
const char* TOPIC_EVENTS = "citizen-assist-ai/fiap-1cc-fev-demo-2026/events";
const char* TOPIC_STATE = "citizen-assist-ai/fiap-1cc-fev-demo-2026/state";
const int BTN_ADD=18, BTN_DONE=19, LED_GREEN=25, LED_RED=26, BUZZER=27;
WiFiClient wifiClient; PubSubClient mqtt(wifiClient); Adafruit_SSD1306 display(128,64,&Wire,-1);
int queueSize=0, completed=0; float estimated=0;
bool errorEmpty=false; unsigned long lastHB=0, lastAdd=0,lastDone=0;
unsigned int sequence=0;

void render(){
 display.clearDisplay();display.setTextColor(SSD1306_WHITE);display.setTextSize(1);
 display.setCursor(0,0); display.println("CITIZEN ASSIST AI");display.println("-------------------");
 if(errorEmpty)display.println("FILA VAZIA!");else {display.print("Fila: ");display.println(queueSize);}
 display.print("Concluidos: ");display.println(completed);display.print("Espera IA: ");display.print(estimated,1);display.println(" min");display.display();
 digitalWrite(LED_GREEN,queueSize>0&&!errorEmpty);digitalWrite(LED_RED,errorEmpty);
}
void onMessage(char* topic, byte* payload, unsigned int length){
 StaticJsonDocument<256> d; if(deserializeJson(d,payload,length))return;
 if(d.containsKey("queue")){queueSize=d["queue"].as<int>();completed=d["completed"].as<int>();estimated=d["wait"].as<float>();errorEmpty=false;}
 const char* err=d["error"] | "";if(strlen(err)>0){errorEmpty=true;tone(BUZZER,900,250);}
 render();
}
void connectMqtt(){
 while(!mqtt.connected()){
  String cid="fiap-esp32-"+String((uint32_t)ESP.getEfuseMac(),HEX);
  if(mqtt.connect(cid.c_str())){mqtt.subscribe(TOPIC_STATE);Serial.println("[rede] MQTT conectado a broker.hivemq.com");}
  else {Serial.print("[rede] Falha MQTT: ");Serial.println(mqtt.state());delay(1500);}
 }
}
void sendEvent(const char* kind){
 StaticJsonDocument<192> d; d["type"]=kind;
 d["event_id"]=String((uint32_t)ESP.getEfuseMac(),HEX)+"-"+String(millis())+"-"+String(++sequence);
 char buffer[192];serializeJson(d,buffer);mqtt.publish(TOPIC_EVENTS,buffer);
 Serial.print("[botao] ");Serial.println(kind);
}
void setup(){
 Serial.begin(115200);pinMode(BTN_ADD,INPUT_PULLUP);pinMode(BTN_DONE,INPUT_PULLUP);
 pinMode(LED_GREEN,OUTPUT);pinMode(LED_RED,OUTPUT);pinMode(BUZZER,OUTPUT);
 Wire.begin(21,22);display.begin(SSD1306_SWITCHCAPVCC,0x3C);render();
 WiFi.begin("Wokwi-GUEST","",6);while(WiFi.status()!=WL_CONNECTED){delay(350);Serial.print(".");}
 Serial.println("\n[rede] Wi-Fi conectado");mqtt.setServer(BROKER,1883);mqtt.setCallback(onMessage);connectMqtt();
}
void loop(){
 if(!mqtt.connected())connectMqtt();mqtt.loop();
 unsigned long t=millis();
 if(digitalRead(BTN_ADD)==LOW && t-lastAdd>350){lastAdd=t;sendEvent("arrival");}
 if(digitalRead(BTN_DONE)==LOW && t-lastDone>350){lastDone=t;sendEvent("complete");}
 if(t-lastHB>10000){lastHB=t;mqtt.publish(TOPIC_EVENTS,"{\"type\":\"heartbeat\"}");}
 delay(20);
}
