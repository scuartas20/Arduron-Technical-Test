#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del botón del ESP32.
Este script simula las solicitudes que haría el ESP32 cuando se presiona el botón.
"""

import asyncio
import json
import websockets
from datetime import datetime

# Configuración
BACKEND_URL = "ws://localhost:5000/ws/DOOR-001"

async def simulate_button_press():
    """Simula la presión del botón del ESP32."""
    try:
        # Conectar al WebSocket del backend
        async with websockets.connect(BACKEND_URL) as websocket:
            print("🔌 Conectado al backend como DOOR-001")
            
            # Simular handshake inicial
            handshake = {
                "type": "status_update",
                "data": {
                    "physical_status": "closed"
                },
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(handshake))
            print("📤 Enviado estado inicial")
            
            # Esperar respuesta del handshake
            response = await websocket.recv()
            print(f"📥 Respuesta del backend: {response}")
            
            # Simular presión del botón (puerta cerrada -> solicitar abrir)
            print("\n🔘 Simulando presión del botón (solicitar abrir)...")
            button_request = {
                "type": "button_command_request",
                "command": "open",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(button_request))
            print("📤 Solicitud de botón enviada")
            
            # Esperar respuesta del backend
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Respuesta del backend: {response}")
            
            if response_data.get("type") == "command":
                print("✅ Comando autorizado - Cambiando estado de la puerta")
                # Simular cambio de estado y envío de confirmación
                status_update = {
                    "type": "status_update",
                    "data": {
                        "physical_status": "open"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(status_update))
                print("📤 Estado actualizado enviado")
                
            elif response_data.get("type") == "command_denied":
                print(f"❌ Comando denegado: {response_data.get('reason')}")
                print("🚫 No se cambia el estado de la puerta")
            
            # Esperar un poco más para ver si llegan más mensajes
            try:
                additional_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📥 Mensaje adicional: {additional_response}")
            except asyncio.TimeoutError:
                print("⏱️ No hay mensajes adicionales")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def test_locked_door():
    """Prueba específica para una puerta bloqueada."""
    print("\n" + "="*50)
    print("🔒 PRUEBA: Puerta bloqueada")
    print("="*50)
    
    # Nota: Para esta prueba, primero necesitarías bloquear la puerta
    # usando el frontend o API REST
    print("⚠️ Para esta prueba, primero bloquea DOOR-001 usando:")
    print("   - Frontend: Click en LOCK")
    print("   - O API: POST /api/access_log con command='lock'")
    print()
    
    await simulate_button_press()

async def test_unlocked_door():
    """Prueba específica para una puerta desbloqueada."""
    print("\n" + "="*50)
    print("🔓 PRUEBA: Puerta desbloqueada")
    print("="*50)
    
    await simulate_button_press()

if __name__ == "__main__":
    print("🧪 Iniciando pruebas de funcionalidad del botón ESP32")
    print(f"🌐 Conectando a: {BACKEND_URL}")
    print()
    
    # Ejecutar prueba básica
    asyncio.run(test_unlocked_door())
    
    # Información para prueba manual
    print("\n" + "="*50)
    print("📋 INSTRUCCIONES PARA PRUEBA COMPLETA:")
    print("="*50)
    print("1. Ejecuta el backend: python backend/src/main.py")
    print("2. Abre el frontend: http://localhost:3000")
    print("3. Ejecuta este script para simular botón del ESP32")
    print("4. Observa los logs en tiempo real en el frontend")
    print("5. Cambia el estado de bloqueo y prueba de nuevo")
    print()
    print("🎯 El ESP32 real seguirá el mismo patrón de comunicación")