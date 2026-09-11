# Hybrid Voice Assistant — Architectural Baseline v5

Esta es la auditoría y definición arquitectónica estricta para el Hybrid Voice Assistant, construida analizando el estado actual de los repositorios y la viabilidad técnica real.

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
El flujo conceptual separa la decisión semántica de la ejecución física:
```text
Voice Input
   ↓
Audio Pipeline (VAD -> STT)
   ↓
Transcript
   ↓
NLU (Normalization -> Entity Extraction)
   ↓
Intent
   ↓
Router (¿Qué tipo de operación es esta?)
   ↓
Planner (¿Qué pasos requiere? - Sólo en Workflows o Agents)
   ↓
Task
   ↓
Security Gate (Capability -> Android Permission -> Risk -> User Confirmation)
   ↓
Dispatcher (¿Qué componente debe ejecutar esta tarea?)
   ↓
Executor (¿Cómo ejecuto físicamente esta operación?)
   ↓
ExecutionResult
```

## 4. Runtime Ownership
- **Runtime Owner:** Android Application. Kotlin es el anfitrión.
- **Lifecycle Owner:** Android Service. Mantiene vivos tanto al Thread nativo como a Python. Si Android mata el proceso, se pierde todo lo no persistido.
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
El puente no expone Android a Python, sino que transporta comandos abstractos validados.
**Definición conceptual de contratos (No es código implementado):**
- **AndroidCommand**:
  - Propósito: Instrucción abstracta desde Python para ejecución en Kotlin.
  - Productor: Python (Dispatcher/Skill).
  - Consumidor: Kotlin (Android Bridge Receiver).
  - Datos mínimos: `id`, `type`, `action`, `payload`, `timeout`, `risk_level`.
  - Errores/Cancelación: Timeout implícito en la capa de Kotlin. Si cancelado, Kotlin desestima ejecución.
- **AndroidResult**:
  - Propósito: Respuesta estructurada sobre el éxito o fracaso de la acción nativa.
  - Productor: Kotlin.
  - Consumidor: Python.
  - Datos mínimos: `command_id`, `status` (SUCCESS/ERROR), `data`, `error_details`.
- **Capability**:
  - Propósito: Identificador de permiso interno del sistema.
  - Productor: Skill.
  - Consumidor: Security Gate (Python).
- **ConfirmationRequest**:
  - Propósito: Suspender ejecución hasta tener aval del usuario.
  - Productor: Security Gate (Python).
  - Consumidor: Kotlin UI / TTS.

**ARCHITECTURAL DECISION PENDING:** Mecanismo físico del puente. Si se usa Chaquopy, puede ser proxy directo. Si es JNI puro, deberá ser IPC/Local Socket (preferido para aislar crasheos) pasando JSON o Protobuf.

## 9. Audio Architecture
- Origen: Micrófono Android (AudioRecord).
- Todo el procesamiento continuo debe residir en Kotlin/C++ dentro de un Foreground Service. Enviar flujo PCM ininterrumpido a Python agotaría la batería y bloquearía el Bridge.

## 10. Wake Word
**ARCHITECTURAL DECISION PENDING**
- Requisitos: Español, Offline, Bajo consumo, C++/Kotlin.
- Evaluaciones a realizar: openWakeWord (viabilidad de ejecución en TFLite nativo), Porcupine (validar si licencia comercial es un bloqueante).

## 11. VAD
**CONFIRMED:** Debe ejecutarse en C++/Kotlin justo después del Wake Word para segmentar el audio y evitar despertar a Python o al motor STT con ruido ambiental.
Flujo: `WakeWord -> VAD inicia captura -> silencio detectado -> VAD corta -> STT procesa`.

## 12. STT Offline
**ARCHITECTURAL DECISION PENDING**
- Requisitos: Precisión aceptable en Español, Offline, Baja latencia, RAM contenida.
- Opciones: `whisper.cpp` (preferido por versatilidad C/JNI, pero pesado en RAM), Android native SpeechRecognizer (ligero, pero fiabilidad varía por fabricante).

## 13. NLU & Router vs Planner vs Dispatcher
- **NLU:** Normaliza y extrae entidades estáticas (Reglas/Regex).
- **Router:** Determina la intención y asigna el ExecutionMode: DIRECT, WORKFLOW, AGENT, LLM.
- **Planner:** Se activa si es WORKFLOW o AGENT para desgranar un array de sub-tareas.
- **Dispatcher:** Decide a qué componente de ejecución le entrega el *Task*.

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
- **Reutilizable:** SÍ. Debemos aislar su dependencia de ADB actual. Su AccessibilityService puede activarse solicitando permiso directo en Android.
- **Determinista:** Proporciona un mecanismo determinista de inyección (click, texto) si se le proveen las coordenadas o Node IDs correctos.

## 17. DroidRun (Agent Legacy)
**CONTRADICTED:** "DroidRun es análisis visual puro" es INCORRECTO. El código original de `mobilerun` extrae el árbol de UI mediante Accesibilidad (Portal) y se lo da a un LLM en texto/XML, no usando procesamiento de imágenes puro.
- **DEPRECATE:** El flujo actual `ManagerAgent` y `ExecutorAgent` que llama continuamente a LlamaIndex.
- **ADAPT:** `DroidRunExecutor` debe convertirse en el fallback aislado de automatización.

## 18. LLM (Gateway)
- **¿Es LlamaIndex Requerido?** **CONTRADICTED**. Aumenta drásticamente el peso del APK y trae docenas de dependencias irrelevantes para un asistente en local.
- **Recomendación:** **REMOVE/REDUCE**. Mover los prompts y schemas (estructurados) a implementaciones raw usando Pydantic + el cliente HTTP directo.

## 19. Security, Permissions y Confirmation
**INFERRED:** La arquitectura forzará el siguiente flujo en Python:
1. `Capability Check:` ¿Soporta la app esta acción?
2. `Android Permission:` Si Kotlin rechaza (Permission denied), abortar con error.
3. `Risk:` Evaluar si la acción (ej. `SEND_SMS`) está clasificada como HIGH o CRITICAL.
4. `Confirmation:` Levantar evento a UI. Pausar la ejecución. Esperar respuesta del usuario.
Un LLM jamás saltará este flujo porque generará un payload validado, no un shell script libre.

## 20. Cancellation
El comando global "Cancela" detendrá:
- El STT en curso.
- Tareas `asyncio` pendientes en Workflows.
- LLMs en generación.
- Confirmaciones pendientes (marcadas como descartadas).

## 21. State & 22. Memory
- **Ephemeral:** Contexto de la orden viva. Tareas en RAM.
- **Recoverable:** Tareas pasadas al Android Bridge que sobreviven si Python cae.
- **Persistent:** SQLite para `User Preferences` (Configuraciones, Alarmas locales de Python).
- **Semantic:** Fuera del alcance (Planeado futuro).

## 23. Persistence
SQLite (Librería nativa de Python `sqlite3`) como único store persistente. No usar PostgreSQL, Redis ni VectorDB.

## 24. Events
- **EventBus Python:** Mantenido para comunicación intra-proceso (logging, telemetría).
- **Python-Kotlin Bridge:** No es un EventBus, debe usar Commands/Callbacks asíncronos explícitos para no perder trazabilidad.

## 25. Error Handling
- Si falla STT -> Clarification.
- Si falla Router determinista -> Pasa a Local LLM para entendimiento semántico.
- Si Android API falla -> Falla la tarea, no hace fallback a DroidRun a menos que esté expresamente programado.

## 26. Offline Modes
- **FULL OFFLINE:** Skills nativas y NLU regex.
- **LOCAL AI OFFLINE:** Si un modelo LLM offline es integrado.
- **ONLINE:** Para APIs Cloud o LLM pesado.
- Si no hay red, un task Cloud falla de inmediato y hace downgrade a Local/Clarification.

## 27. Observability
- Python Logging estándar exportado al Logcat de Android.

## 28. Testing Strategy
- **NO-LLM TESTS:** Validar que `Texto -> NLU -> Router -> Skill -> Bridge Command` se ejecute 100% offline, sin invocar LLMs ni red.
- **Bridge Tests:** Validar el parseo de comandos en la frontera JNI/Socket.

## 29. Dependencies
- **REQUIRED:** `pydantic`, `sqlite3`, cliente HTTP asíncrono (`httpx`).
- **CANDIDATE FOR REMOVAL:** `llama-index` y todos sus plugins derivados (inflan el APK y el footprint de memoria).

## 30. Current vs Target
- **Current:** Repositorio en PC (`mobilerun`), depende de ADB local y empuja ciclos continuos de razonamiento a la nube (LlamaIndex).
- **Target:** App residente en Android. Acciones ejecutadas en base a reglas NLU sin red, usando IA como razonador opcional.

## 31. Migration Strategy
1. **No implementar nada.**
2. Ejecutar PoCs (Python Runtime, STT, WakeWord).
3. Iniciar el App Android Shell (Kotlin).
4. Implementar Android Bridge.
5. Embeber `core/` abstracto.

---

## Registro de Decisiones (ADR)

| ID | Decisión | Estado | Evidencia / Notas | Motivo |
| :--- | :--- | :--- | :--- | :--- |
| ADR-001 | Python Runtime Embebido | PENDING | `POC_REQUIRED` | Necesitamos medir peso del APK, soporte `asyncio` y JNI vs Chaquopy. |
| ADR-002 | Android Bridge por Command/Result | PENDING | `POC_REQUIRED` | JNI vs IPC local socket. Depende directamente de ADR-001. |
| ADR-003 | Wake Word Offline | PENDING | `POC_REQUIRED` | openWakeWord vs Porcupine. A probar impacto de batería. |
| ADR-004 | VAD en Kotlin/C++ | ACCEPTED | `INFERRED` de OS. | Para segmentar antes del puente Python y ahorrar batería. |
| ADR-005 | STT Offline Local | PENDING | `POC_REQUIRED` | Whisper.cpp vs Native SpeechRecognizer. Evaluación de WER y RAM. |
| ADR-006 | Portal reusado sin ADB | ACCEPTED | `CONFIRMED` en repo local. | Portal usa `AccessibilityService`, activable por UI en producción, sin ADB. |
| ADR-007 | DroidRun como Fallback | ACCEPTED | `CONFIRMED` en `mobilerun`. | UI Automation asume control total visual y es frágil. Limitar a `DroidRunExecutor`. |
| ADR-008 | Eliminación de LlamaIndex | ACCEPTED | `CONFIRMED` vía pyproject.toml | Acopla fuertemente el workflow y añade peso insostenible para Mobile. |

---

# GO / NO-GO PARA IMPLEMENTACIÓN

**GO WITH POC:**
La dirección arquitectónica general de separación de responsabilidades y priorización Native-First está consolidada. Se puede avanzar a la implementación, pero **SOLO DESPUÉS** de completar satisfactoriamente los siguientes PoCs bloqueantes de la arquitectura base:

**POC REQUIRED (BLOCKED PARA IMPLEMENTACIÓN DE CÓDIGO FINAL DE PRODUCCIÓN):**
- **ADR-001 y ADR-002:** Selección e integración del Python Runtime Embebido en Android (Chaquopy vs JNI) y definición técnica del puente asíncrono (IPC vs JNI Calls). El core no puede programarse eficientemente sin saber cómo interactuará el event loop de Python con Android.
- **ADR-003 y ADR-005:** Viabilidad técnica de empaquetar y ejecutar un modelo WakeWord/STT Offline para Español en un dispositivo móvil con latencia aceptable.
