#include "Adafruit_MAX31855.h"
#include <Arduino.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <WebSocketsServer.h>
#include <WiFiManager.h>

// Pinos SPI livres na TTGO T-Beam
#define MAXDO 13  // MISO
#define MAXCS 15  // CS
#define MAXCLK 14 // SCK

Adafruit_MAX31855 thermocouple(MAXCLK, MAXCS, MAXDO);
WebSocketsServer webSocket(81);

int clientesConectados = 0;

bool verificarSensor(double &tempExt, double &tempInt, uint8_t &erro) {
  tempExt = thermocouple.readCelsius();
  tempInt = thermocouple.readInternal();
  erro = thermocouple.readError();

  if (isnan(tempExt) || erro != 0 || (tempExt == 0.0 && tempInt == 0.0)) {
    return false;
  }
  return true;
}

void onWebSocketEvent(uint8_t num, WStype_t type, uint8_t *payload,
                      size_t length) {
  switch (type) {
  case WStype_DISCONNECTED:
    if (clientesConectados > 0)
      clientesConectados--;
    Serial.printf("[%u] Cliente desconectado\n", num);
    break;

  case WStype_CONNECTED:
    clientesConectados++;
    Serial.printf("[%u] Cliente conectado via IP: %s\n", num,
                  webSocket.remoteIP(num).toString().c_str());
    break;

  case WStype_TEXT: {
    StaticJsonDocument<128> reqDoc;
    DeserializationError err = deserializeJson(reqDoc, payload, length);
    if (err) {
      Serial.println("Erro ao parsear JSON recebido");
      return;
    }

    long msgId = reqDoc["id"] | 0;
    const char *command = reqDoc["command"] | "";

    if (strcmp(command, "getData") == 0) {
      double tempExt, tempInt;
      uint8_t erro;
      bool conectado = verificarSensor(tempExt, tempInt, erro);

      StaticJsonDocument<128> resDoc;
      resDoc["id"] = msgId;
      resDoc["data"]["BT"] = conectado ? tempExt : 0.0;

      String response;
      serializeJson(resDoc, response);
      webSocket.sendTXT(num, response);
    }
    break;
  }
  default:
    break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n--- Iniciando ESP32 Torrador ---");

  if (!thermocouple.begin()) {
    Serial.println("ERRO: Falha ao inicializar a biblioteca MAX31855!");
  }
  pinMode(MAXDO, INPUT_PULLUP);
  delay(100);

  WiFiManager wm;
  Serial.println("Conectando ao WiFi...");
  // Tenta conectar com credenciais salvas. Se falhar, sobe o portal
  // "ESP32_Torrador_Config" pra você digitar SSID/senha pelo celular.
  bool res = wm.autoConnect("ESP32_Torrador_Config");

  if (!res) {
    Serial.println("Falha ao conectar. Reiniciando o ESP32...");
    delay(1000);
    ESP.restart();
  }

  Serial.println("\nWiFi conectado!");
  Serial.print("IP para configurar no Artisan: ");
  Serial.println(WiFi.localIP());
  Serial.println("Porta: 81 | Path: /");

  webSocket.begin();
  webSocket.onEvent(onWebSocketEvent);
  Serial.println("Servidor WebSocket pronto. Aguardando conexão...\n");
}

void loop() {
  webSocket.loop();

  static unsigned long lastWifiCheck = 0;
  if (millis() - lastWifiCheck >= 10000) {
    lastWifiCheck = millis();
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[WiFi] Conexão perdida. Tentando reconectar...");
      WiFi.reconnect();
    }
  }

  static unsigned long lastLog = 0;
  static bool avisoDesconectadoExibido = false;

  if (millis() - lastLog >= 1500) {
    lastLog = millis();

    double tempExt, tempInt;
    uint8_t erro;
    bool ok = verificarSensor(tempExt, tempInt, erro);

    if (ok) {
      avisoDesconectadoExibido = false;
      if (clientesConectados > 0) {
        Serial.printf("[Conectado] Temp: %.2f °C\n", tempExt);
      }
    } else {
      if (!avisoDesconectadoExibido) {
        Serial.println("[Aviso] MAX31855 DESCONECTADO (verifique pinos 13-DO, "
                       "15-CS, 14-CLK)");
        avisoDesconectadoExibido = true;
      }
    }
  }
}