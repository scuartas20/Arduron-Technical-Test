#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "XXXX";           // Change to your WiFi network
const char* password = "XXXXX";    // Change to your WiFi password

// WebSocket server settings
const char* websocket_server = "192.168.1.XX";  // Change to your backend IP
const int websocket_port = 5000;
const char* websocket_path = "/ws/DOOR-001";

// GPIO pins
const int LED_RED = 16;    // Red LED - door closed
const int LED_GREEN = 17;  // Green LED - door open  
const int SWITCH_PIN = 14; // Manual switch

// Door state
bool doorOpen = false;
bool lastSwitchState = false;
bool currentSwitchState = false;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// WebSocket client
WebSocketsClient webSocket;

void setup() {
  Serial.begin(115200);
  
  // Configure GPIO pins
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(SWITCH_PIN, INPUT_PULLDOWN);
  
  // Initialize door as closed
  setDoorState(false);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("WiFi connected! IP: ");
  Serial.println(WiFi.localIP());
  
  // Initialize WebSocket connection
  webSocket.begin(websocket_server, websocket_port, websocket_path);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  
  Serial.println("ESP32 DOOR-001 started");
  Serial.println("Red LED (GPIO16): Door closed");
  Serial.println("Green LED (GPIO17): Door open");
  Serial.println("Switch (GPIO14): Manual control");
}

void loop() {
  webSocket.loop();
  handleSwitchInput();
  delay(10);
}

void setDoorState(bool open) {
  doorOpen = open;
  
  if (doorOpen) {
    // Door open: Green LED ON, Red LED OFF
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(LED_RED, LOW);
    Serial.println("🟢 Door OPEN");
  } else {
    // Door closed: Red LED ON, Green LED OFF
    digitalWrite(LED_RED, HIGH);
    digitalWrite(LED_GREEN, LOW);
    Serial.println("🔴 Door CLOSED");
  }
}

void handleSwitchInput() {
  int reading = digitalRead(SWITCH_PIN);
  
  // Debounce logic
  if (reading != lastSwitchState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != currentSwitchState) {
      currentSwitchState = reading;
      
      // Switch pressed (LOW to HIGH transition)
      if (currentSwitchState == HIGH) {
        Serial.println("🔘 Switch pressed - Requesting door state change");
        
        // Instead of changing state directly, send a command request to backend
        String command = doorOpen ? "close" : "open";
        sendCommandRequest(command);
      }
    }
  }
  
  lastSwitchState = reading;
}

void sendStatusUpdate() {
  if (webSocket.isConnected()) {
    // Create JSON message for status update
    DynamicJsonDocument doc(1024);
    doc["type"] = "status_update";
    doc["data"]["physical_status"] = doorOpen ? "open" : "closed";
    doc["timestamp"] = getTimestamp();
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("📤 Status sent to backend: " + message);
  } else {
    Serial.println("⚠️ WebSocket not connected - Could not send status");
  }
}

void sendCommandRequest(String command) {
  if (webSocket.isConnected()) {
    // Create JSON message for command request from physical button
    DynamicJsonDocument doc(1024);
    doc["type"] = "button_command_request";
    doc["command"] = command;
    doc["timestamp"] = getTimestamp();
    
    String message;
    serializeJson(doc, message);
    
    webSocket.sendTXT(message);
    Serial.println("📤 Button command request sent to backend: " + message);
  } else {
    Serial.println("⚠️ WebSocket not connected - Could not send command request");
  }
}

void sendCommandResponse(String command, bool success, String message) {
  if (webSocket.isConnected()) {
    DynamicJsonDocument doc(1024);
    doc["type"] = "command_response";
    doc["command"] = command;
    doc["success"] = success;
    doc["message"] = message;
    doc["timestamp"] = getTimestamp();
    
    String response;
    serializeJson(doc, response);
    
    webSocket.sendTXT(response);
    Serial.println("📤 Response sent: " + response);
  }
}

String getTimestamp() {
  // Simple timestamp - in production you could use NTP
  return String(millis());
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("🔌 WebSocket Disconnected");
      break;
      
    case WStype_CONNECTED:
      Serial.printf("🔌 WebSocket Connected to: %s\n", payload);
      // Send initial status
      sendStatusUpdate();
      break;
      
    case WStype_TEXT:
      Serial.printf("📥 Message received: %s\n", payload);
      handleWebSocketMessage((char*)payload);
      break;
      
    case WStype_ERROR:
      Serial.printf("❌ WebSocket Error: %s\n", payload);
      break;
      
    default:
      break;
  }
}

void handleWebSocketMessage(String message) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.println("❌ JSON parsing error: " + String(error.c_str()));
    return;
  }
  
  String type = doc["type"];
  
  if (type == "command") {
    String command = doc["command"];
    Serial.println("🎯 Command received: " + command);
    
    if (command == "open") {
      if (!doorOpen) {
        setDoorState(true);
        sendCommandResponse("open", true, "Door opened successfully");
        sendStatusUpdate(); // Send updated status
      } else {
        sendCommandResponse("open", true, "Door was already open");
      }
    }
    else if (command == "close") {
      if (doorOpen) {
        setDoorState(false);
        sendCommandResponse("close", true, "Door closed successfully");
        sendStatusUpdate(); // Send updated status
      } else {
        sendCommandResponse("close", true, "Door was already closed");
      }
    }
    else {
      sendCommandResponse(command, false, "Unknown command");
    }
  }
  else if (type == "command_denied") {
    String command = doc["command"];
    String reason = doc["reason"];
    Serial.println("❌ Command DENIED: " + command + " - Reason: " + reason);
    // Don't change state, just log the denial
  }
  else if (type == "handshake") {
    Serial.println("🤝 Handshake received from server");
    // Send current status after handshake
    sendStatusUpdate();
  }
  else if (type == "ack") {
    Serial.println("✅ Acknowledgment received from server");
  }
  else {
    Serial.println("⚠️ Unknown message type: " + type);
  }
}