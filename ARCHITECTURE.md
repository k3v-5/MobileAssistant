# Hybrid Voice Assistant — Architectural Baseline v4

Esta es la auditoría y definición arquitectónica estricta para el Hybrid Voice Assistant, construida analizando el estado actual de los repositorios y la viabilidad técnica real. Todas las secciones se basan en investigación y desmienten suposiciones prematuras de versiones previas.

---

## 1. Product Goal
Crear un asistente de voz residente en Android, operando bajo un paradigma Híbrido, Deterministic-first y Offline-first. Se separa de la dependencia heredada en la automatización visual por IA (DroidRun) priorizando APIs nativas (Android Intents, Content Providers, etc.).

## 2. Physical Architecture
```text
Android Device
 ├── Android OS
 │    ├── Kotlin/Java (Native Layer & Host)
 │    │    ├── Wake Word & VAD (C++)
 │    │    ├── Microphone & TTS
 │    │    ├── Android Execution Mechanisms (Intents/Managers)
 │    │    └── Android Bridge
 │    │
 │    ├── Python Core (Embedded Runtime)
 │    │    ├── Router / Planner / Dispatcher
 │    │    ├── Skills
 │    │    └── Local/Cloud LLM Gateways
 │    │
 │    └── Portal (Accessibility Service)
 │         └── Deterministic / LLM-guided Screen execution
```

## 3. Logical Architecture
```text
Voice
  ↓
STT (Native Layer)
  ↓
Transcript
  ↓
NLU (Normalization & Entity Extraction - Python)
  ↓
Intent
  ↓
Router (¿Qué tipo de operación es esta?)
  ↓
Planner (¿Qué pasos requiere? - Sólo en Workflows o Agents)
  ↓
Dispatcher (¿Qué módulo de Python debe ejecutar esta tarea?)
  ↓
Security Gate (Risk Evaluation / Confirmations)
  ↓
Executor (Preparación del comando por la Skill)
  ↓
ExecutionResult
```

## 4. Runtime Ownership
- **Runtime Owner:** Android Application. Kotlin es el anfitrión.
- **Lifecycle Owner:** Android Service. Mantiene vivos tanto al Thread nativo como a Python. Si Android mata el proceso, se pierde todo lo no persistido en SQLite.
- **State Owner:** SQLite (Persistent) y Kotlin Memory (WakeWord Buffer). Python mantiene memoria `Ephemeral` (ej. Event loops).

## 5. Python Runtime Strategy (en Android)
**ARCHITECTURAL DECISION PENDING**
- Chaquopy: Excelente integración Java-Python pero infla el APK y se amarra al build system Gradle (dificulta dependencias pesadas en C/C++ modernas).
- JNI Embebido o Python-for-Android/Kivy: Menos integrado pero más ligero y controlable.
- Necesita validación cruzando asyncio, SQLite, Pydantic y llamadas HTTP concurrentes en background.

## 6. Kotlin Responsibilities
- Lifecycle management (Foreground Services).
- Gestión del ciclo continuo del micrófono y permisos hardware.
- Instanciación y anclaje del Python Runtime.
- Puerta final de ejecución hacia Android (ContentResolver, Intents, AudioManager).
- TTS nativo offline.

## 7. Python Responsibilities
- Recepción de Transcript.
- Normalización y Extracción determinista.
- Ruling y planificación de tareas lógicas (Skills).
- Abstracción hacia LLMs.
- Confección estricta de la firma tipada de las herramientas (Pydantic schemas).

## 8. Android Bridge & Contratos
El puente no expone Android a Python, sino que transporta comandos abstractos validados:
- **`AndroidCommand`**: Creado por Python, consumido por Kotlin. Contiene `{type: str, action: str, payload: dict}`.
- **`AndroidResult`**: Creado por Kotlin, devuelto a Python. Contiene `{status: SUCCESS/ERROR, data: dict}`.
- **ARCHITECTURAL DECISION PENDING:** Mecanismo. Si se usa Chaquopy, puede ser proxy de objetos de Python a Java. Si es JNI puro, deberá ser un canal de paso de JSON/Protobufs.

## 9. Audio Architecture
- Kotlin asume el control del Microphone en un Foreground Service para minimizar consumo de batería y mantener los permisos de Android frente a cierres forzosos.

## 10. Wake Word
**ARCHITECTURAL DECISION PENDING**
- Requisito: Bajo consumo, offline, sin latencia, en español. Debe evaluarse OpenWakeWord (Si se puede aislar su inferencia de TFLite o ONNX nativo) u otros motores Edge (Picovoice requiere licencia comercial que limita opensource).

## 11. VAD
**CONFIRMED:** Debe ejecutarse justo después del Wake Word en C++/Kotlin, para segmentar el audio antes de llamar al motor de transcripción, evitando que Python trabaje con silencios y protegiendo la batería.

## 12. STT
**ARCHITECTURAL DECISION PENDING**
- Evaluar `whisper.cpp` mediante JNI vs Google Offline Speech Recognition (nativo Android). Depende del balance precisión en español/latencia.

## 13. NLU & Router vs Planner vs Dispatcher
- **NLU:** Normaliza y extrae entidades estáticas (Reglas/Regex).
- **Router:** Determina si el intent corresponde a ExecutionMode: DIRECT, WORKFLOW, AGENT, LLM.
- **Planner:** Se activa si es WORKFLOW o AGENT para desgranar un array de sub-tareas.
- **Dispatcher:** Decide a qué *Skill* (Python object) le entrega el *Task*.

## 14. Skills
Representan un dominio lógico (`AlarmSkill`, `CalendarSkill`). Evalúan los parámetros (Entidades) con Pydantic y generan un `AndroidCommand` seguro.

## 15. Mobile Execution Layer (Capa Nativa)
Es quien ejecuta físicamente el `AndroidCommand` desde Kotlin:
- **Native Android API**: AlarmManager, TelecomManager.
- **Local APIs / Content Providers**: CalendarProvider, ContactsContract.
- **Android Intents**: `android.intent.action.SET_ALARM`, Deep Links.
- **Accessibility (Portal)**.

## 16. Portal
**CONFIRMED:** Existe en el proyecto original en `mobilerun_core_local.driver.android.portal`. Es un servicio de accesibilidad Android.
- **Requiere ADB:** Sí, el setup legacy lo levanta y configura a través de comandos shell de ADB (`ensure_portal_ready`, `toggle_socket_server`).
- **Deterministico:** Parcialmente. Su API TCP es determinista, pero los componentes legacy lo alimentan con coordinates generadas por un LLM.
- **Reutilizable:** SÍ. Debemos aislar su dependencia de ADB para invocar su Accessibility Service nativamente en local.

## 17. DroidRun (Agent Legacy)
**CONTRADICTED:** "DroidRun es análisis visual puro" es **INCORRECTO**. DroidRun (Mobilerun) extrae el Accessibility UI Tree usando Portal y lo inyecta a un LLM en formato textual/XML, reservando el procesamiento visual (Screenshots) como complemento o modo fallback visual, pero no es puramente "visión" en el sentido de OCR, se basa fuertemente en Accessibility.

Auditoría de `mobilerun/agent`:
- `FastAgent` / `ManagerAgent` / `ExecutorAgent`: Fuertemente acoplados a `llama-index` y `llama-index-workflows`. **DEPRECATE** (O **ISOLATE** como módulo `UI_AGENT` final estricto, si se migra).

## 18. LLM (Gateway)
- **¿Es LlamaIndex Requerido?** **CONTRADICTED**. No lo necesitamos en el producto final. Aumenta drásticamente el peso del APK y trae docenas de dependencias irrelevantes para un asistente en local.
- **Recomendación:** **REMOVE/REDUCE**. Mover los prompts y schemas (estructurados) a implementaciones raw usando Pydantic + el cliente API directo (OpenAI, Gemini o endpoint local HTTP llama.cpp).

## 19. Security, Permissions y Confirmation
**INFERRED:** La arquitectura forzará el siguiente flujo en Python (antes de llegar a Android):
1. `Capability Check:` ¿Soporta la app esta acción?
2. `Android Permission:` El comando exige permiso nativo. Si Kotlin rechaza (Permission denied), abortar con error.
3. `Risk:` Evaluar si la acción (ej. `SEND_SMS`) está clasificada como HIGH o CRITICAL.
4. `Confirmation:` Levantar evento a UI. Pausar la ejecución. Esperar True/False del usuario (Botón UI o respuesta vocal "Sí").

## 20. Cancellation
El comando global "Cancela" debe capturarse en STT/Router y anular el `asyncio.Task` del flujo activo (si es un Workflow en Python) o rechazar un ConfirmationRequest pendiente.

## 21. State & 22. Memory
- **Ephemeral:** Contexto de la orden viva. Tareas en RAM.
- **Recoverable:** Tareas pasadas al Android Bridge que sobreviven si Python cae (Ej. Intent envíado a Telegram).
- **Persistent:** SQLite para `User Preferences` (Configuraciones de App por defecto, Thresholds).
- **Semantic:** Fuera del alcance (Planeado futuro).

## 23. Persistence
SQLite (Librería nativa de Python `sqlite3`) como único store persistente por ahora. No usar PostgreSQL, Redis ni Chroma.

## 24. Events
No convertir toda comunicación de cruce en Eventos. Usar `Commands/Callbacks` para llamadas al Bridge y `EventBus` in-memory de Python puramente intra-proceso (Logs, tracing).

## 25. Error Handling
- Si no hay match (Router), NO saltar a DroidRun. Saltar a un LLM para Clarification (Hablar con el usuario).
- Si el Bridge falla (Android Exception), abortar orden y devolver error determinista.

## 26. Offline Modes
- **FULL OFFLINE:** Skills nativas, Alarmas, Rutinas Deterministas, NLU regex.
- **LOCAL AI OFFLINE:** Razonamiento complejo/Summary usando modelos inferidos localmente.
- **ONLINE:** Peticiones externalizadas (Spotify APIs, Búsquedas, Cloud LLMs cuando Local falla).

## 27. Observability
- Python Logging estándar exportado al Logcat de Android.

## 28. Testing
Categorías críticas:
- **NO-LLM TESTS:** Probar la cadena (Transcript -> NLU -> Router -> Skill -> Mock Android Bridge) asegurando que no se instancia ninguna IA ni requiere Internet.

## 29. Dependencies
- **REQUIRED:** `pydantic` (Schemas/Validations), `sqlite3`.
- **CANDIDATE FOR REMOVAL:** `llama-index`, `async_adbutils` (En producción en Android, no aplica ADB por socket).

## 30. Current vs Target
- **Current:** Repositorio en PC (`mobilerun`), depende de ADB local para inyectar scripts al móvil, extrae UI Nodes del Portal (`mobilerun_core_local`) y empuja ciclos continuos de razonamiento a la nube (LlamaIndex).
- **Target:** App residente en Android. Acciones ejecutadas en base a reglas NLU sin tocar la red, ejecutando Intents y Content Providers desde Kotlin. DroidRun UI Automation es una capacidad aislada de último recurso.

## 31. Migration Strategy
1. Investigar PoC Técnico (**ARCHITECTURAL DECISIONS PENDING**).
2. Congelar dependencias de `mobilerun/`.
3. Iniciar el App Android Shell (Kotlin).
4. Implementar Android Bridge y comunicación nativa.
5. Embeber `core/` y conectar el NLU.

## 32. Pending Decisions
- Python Embedding Engine (Chaquopy vs JNI).
- Android Wake Word engine (offline/bajo consumo).
- Android STT engine (offline).

## 33. Risks
- Restricciones de accesibilidad de Google Play limitando a Portal.
- Peso extremo del APK.
- Desgaste de batería por VAD ineficiente.

---

## 34. Registro de Decisiones (ADR)

| ID | Decisión | Estado | Evidencia / Notas | Motivo |
| :--- | :--- | :--- | :--- | :--- |
| ADR-001 | Android es runtime principal | ACCEPTED | Confirmado. | Proyecto "móvil" no debe depender de PC local. |
| ADR-002 | Python es Core Lógico | ACCEPTED | Código `core/`. | Aprovechar NLU/Pydantic/Orquestación. |
| ADR-003 | Kotlin controla HW y OS | ACCEPTED | Diseño. | Batería, Foreground Services, Audio Nativo. |
| ADR-004 | DroidRun es Fallback (Accesibilidad) | ACCEPTED | Auditoría de `mobilerun/`. | UI automation es frágil. APIs nativas primero. |
| ADR-005 | STT y VAD cruzan frontera | PENDING | No hay PoC. | Evaluar latencia y uso de JNI vs Native. |
| ADR-006 | LlamaIndex Deprecated para Mobile | ACCEPTED | Pyproject deps. | Sobrecarga extrema para un entorno Edge/Mobile. |
| ADR-007 | Portal (A11y) se reutilizará nativamente | ACCEPTED | Código Portal. | Usa A11yService real de Android, extraíble del shell ADB. |
