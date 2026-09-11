# Hybrid Voice Assistant — Architectural Baseline v2

## 1. Objetivo del producto
El producto final es un **asistente de voz residente en el dispositivo Android**. Es un sistema híbrido, offline-first y native-first.
El asistente se compone de Python (actuando como el cerebro de NLU y razonamiento) embebido dentro de una aplicación Android escrita en Kotlin/Java (responsable de la integración nativa y el ciclo de vida del SO). La dependencia de modelos de Inteligencia Artificial (LLMs) se reduce al mínimo indispensable, utilizándolos como razonadores de fallback y no como controladores universales.

## 2. Arquitectura física
```
Android Device
 ├── Android OS
 │    ├── Kotlin/Java (Native Layer)
 │    │    ├── Microphone / Audio APIs
 │    │    ├── Android Intents / APIs
 │    │    └── Android Bridge
 │    │
 │    ├── Python (Embedded Core)
 │    │    ├── NLU / Router
 │    │    ├── Skills
 │    │    └── Local LLM / Cloud API Clients
 │    │
 │    └── Portal (Accessibility/UI Layer)
 │         └── UI Automation / Screen Capture
```
*Aclaración: El PC ya no es el host principal del sistema. ADB queda relegado puramente a desarrollo y debugging.*

## 3. Arquitectura lógica
El sistema separa tajantemente la interpretación (Python) de la ejecución profunda en el sistema operativo (Kotlin). Las tareas se originan desde voz, pasan por un ruteo estricto y, finalmente, se ejecutan en la capa más óptima disponible.

## 4. Responsabilidades Kotlin
- Lifecycle de la App y Foreground Services.
- Gestión del micrófono y audio (AudioRecord).
- Permisos del sistema Android.
- Android Intents y Content Providers.
- Notificaciones y TTS nativo.
- Sensores.
- Comunicación bidireccional (Android ↔ Python).

## 5. Responsabilidades Python
- Contratos de dominio (Pydantic).
- NLU: Transcript, Normalización, Extracción de Entidades.
- Router y Workflows.
- Skills (lógica de negocio abstracta).
- Memoria (estado conversacional).
- Integración con LLM local y Cloud.
- Orquestación del fallback hacia DroidRun.

## 6. Frontera Kotlin/Python
```
Python Core
      ↕
Android Bridge
      ↕
Kotlin
      ↕
Android Framework
```
*Estado:* **ARCHITECTURAL DECISION PENDING**. (Por definir si se usará Chaquopy, proceso separado, JNI o bindings).

## 7. Arquitectura Android
La aplicación actúa como un servicio persistente que atiende peticiones de voz, con permisos suficientes para leer contactos, calendario, y dibujar sobre otras aplicaciones o usar accesibilidad si el fallback (Portal) lo requiere.

## 8. Arquitectura del Core
Las decisiones se toman secuencialmente.
```
Mic → STT → NLU → Router → Permission → Skill → Android Bridge
```

## 9. Audio pipeline
*Estado:* **ARCHITECTURAL DECISION PENDING**.
- *Diseño conceptual:* Micrófono gestionado en Kotlin -> Wake Word local -> VAD -> STT local.
- Determinar dónde cruza el audio hacia Python dependerá del rendimiento y consumo de batería.

## 10. NLU pipeline
Python recibe el transcript textual.
Pasa por: `Normalization -> Entity Extraction -> Intent`.

## 11. Router
Ejecuta la clasificación del Intent en Execution Modes (`DIRECT`, `WORKFLOW`, `LLM`, `AGENT`).

## 12. Skills
Mecanismo principal para tareas deterministas. Una `Skill` (ej: `AlarmSkill`) no llama a Android directamente, sino que envía una orden validada al `Android Bridge`.

## 13. Mobile Execution Layer
Jerarquía de ejecución:
```
1. Deterministic
2. Native Android APIs
3. Local APIs / Content Providers
4. Android Intents / Deep Links
5. Accessibility / Portal
6. Workflow determinista
7. Local LLM
8. Cloud LLM
9. DroidRun Agent + LLM
```

## 14. Portal
El Portal (`appwiz/droidrun` origin) se mantiene. Evoluciona a una capa de capacidades Android/UI estricta (AccessibilityExecutor), consumida sólo cuando no hay alternativa nativa.

## 15. DroidRun
El antiguo framework completo `mobilerun` se degrada a **Fallback**. Se invoca únicamente si el Router determina `ExecutionMode.AGENT` y las Skills/Intents fallaron en resolver la petición.

## 16. LLM Gateway
Prioridad de LLM:
```
No AI → Rules → Deterministic workflow → Local LLM → Cloud LLM
```
El LLM es un razonador opcional, sin acceso irrestricto a la API de Android. Todo output del LLM debe pasar por validación estructurada.

## 17. Seguridad
```
User
 ↓
Intent
 ↓
Task
 ↓
Validation
 ↓
Permission
 ↓
Confirmation
 ↓
Execution
```
Toda operación peligrosa (`HIGH`, `CRITICAL`) requiere intervención explícita.

## 18. Offline-first
La lógica es:
`¿Se puede resolver determinísticamente?` -> SI -> **EJECUTAR**.
*(La falta de internet NUNCA debe obligar a usar un LLM local si existe regla estática)*.

## 19. Memoria
*Estado:* **ARCHITECTURAL DECISION PENDING**.
Prioridad de adopción: RAM -> SQLite -> Semantic Storage.

## 20. Persistencia
La principal persistencia a considerar será SQLite (cuando sea requerida). Nada de bases de datos de servidor pesadas.

## 21. Event system
*Estado:* **ARCHITECTURAL DECISION PENDING**.
Se necesita definir cómo cruzarán los eventos críticos (ej. `speech_detected`, `confirmation_required`) la frontera Python/Kotlin.

## 22. Observabilidad
Trazas claras en Python usando Logging estructurado, midiendo Tokens (cuando aplique IA) y latencia.

## 23. Testing
Las pruebas se dividirán en: Tests Unitarios del Core Python, Tests del Android Bridge y Tests E2E en el dispositivo final.

## 24. Dependencias
Las dependencias en Python deberán purgarse de las pesadas del backend cloud (si no son necesarias) para soportar el empaquetado móvil.

## 25. Estado actual vs objetivo
- **Actual:** El core vive en PC, usa ADB para mover el móvil y LlamaIndex como bucle infinito de razonamiento.
- **Objetivo:** Core vive en móvil, invoca APIs de Kotlin y solo llama a la IA si no existe una regla determinista.

## 26. Decisiones tomadas
- El asistente es una App Android.
- Python es NLU/Router. Kotlin es SO/Hardware.
- DroidRun es fallback, no el orquestador principal.
- Reglas estrictas de seguridad e interrupción antes de la ejecución.

## 27. Decisiones pendientes
- **ARCHITECTURAL DECISION PENDING:** Tecnología exacta para integrar Python en Android (Chaquopy vs JNI vs Otros).
- **ARCHITECTURAL DECISION PENDING:** Tecnología para Wake word, STT Local y VAD dentro de Android vs Python.
- **ARCHITECTURAL DECISION PENDING:** Mecanismo IPC / Eventos Python ↔ Kotlin.

## 28. Riesgos
- Compatibilidad y tamaño del APK al embeber Python y modelos LLM locales.
- Alto consumo de batería si el VAD/Wake Word se gestionan en capas ineficientes de Python.
- Complejidad en la comunicación multihilo (Android Lifecycle vs Python Asyncio).

## 29. Plan de migración desde Mobilerun/DroidRun
1. Congelar características de `mobilerun` (Legacy).
2. Aislar `core/` y refinar sus contratos abstractos.
3. Crear el proyecto Android base y probar el embedding de Python (PoC de frontera Kotlin/Python).
4. Migrar el ruteo estático hacia la app móvil.
5. Deprecar gradualmente la automatización PC-ADB a favor del Native Android Executor.
