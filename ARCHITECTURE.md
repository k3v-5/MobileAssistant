# Hybrid Voice Assistant — Architectural Baseline v3

Este documento define la arquitectura estricta del Hybrid Voice Assistant, estableciendo a Android como el entorno residente, Python como el cerebro lógico, Kotlin como el orquestador del ciclo de vida nativo y limitando el uso de IA (LLMs) a tareas no deterministas.

---

## 1. Product Goal
Un asistente de voz residente 100% en el dispositivo Android, diseñado bajo la filosofía **Offline-first**, **Native-first**, **Deterministic-first**, y **Security-first**. Utiliza modelos LLM únicamente como razonadores de fallback, evitando que tomen el control directo del sistema operativo.

## 2. Physical Architecture
```text
Android Device
 ├── Android OS
 │    ├── Kotlin/Java (Native Host App)
 │    │    ├── Microphone / Audio APIs
 │    │    ├── Android Intents / Providers / Managers
 │    │    └── Android Bridge (Gateway to Python)
 │    │
 │    ├── Python (Embedded Logic Core)
 │    │    ├── NLU / Router / Dispatcher
 │    │    ├── Skills
 │    │    └── Local LLM / Cloud API Clients
 │    │
 │    └── Portal (Accessibility Service)
 │         └── UI Automation / Screen Capture (Fallback)
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
Planner (¿Qué pasos requiere? - Sólo para Workflows/Agents)
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
   ↓
TTS Response
```

## 4. Runtime Ownership
- **Runtime Owner:** Android Application. Kotlin inicia y detiene a Python. Si Android mata el proceso, el estado se pierde a menos que esté persistido.
- **Lifecycle Owner:** Android Service / Foreground Service. Controla la vigencia de la app.
- **Task Owner:** Python Core. Mantiene en memoria el estado del workflow. Si Python falla o reinicia, las tareas en memoria mueren.
- **State Owner:** SQLite (Persistente) / RAM (Efímero).

## 5. Kotlin Responsibilities
- Control del ciclo de vida de la App y Foreground Services.
- Acceso directo al hardware (Microphone) y TTS del OS.
- Interacción con las APIs nativas (AlarmManager, ContentProviders, Intents).
- Mostrar la Interfaz de Usuario y pop-ups de User Confirmation.
- Gestión técnica de los Android Permissions.
- Instanciación y puente de comunicación con el Runtime de Python.

## 6. Python Responsibilities
- Procesamiento NLU (parsing de transcripciones, extracción de entidades).
- Routing semántico (Reglas, Clasificador, Fallback LLM).
- Planificación (Workflows deterministas o Agents).
- Lógica de las "Skills" (preparar payloads validados).
- Manejo de contexto y memoria conversacional.
- Comunicación externa con APIs o LLMs.

## 7. Python Runtime Strategy
**ARCHITECTURAL DECISION PENDING**
- *Opciones:* Chaquopy, Python embebido nativo (e.g., Kivy/BeeWare tools), JNI, proceso separado, bindings.
- *Criterio de decisión:* Requerimos compatibilidad con Python 3.11+, asyncio, dependencias C como SQLite o bindings de Audio, y un peso razonable del APK. Se necesita un PoC antes de decidir.

## 8. Kotlin/Python Boundary & 9. Android Bridge
El **Android Bridge** es un canal tipado y seguro.
- **No es:** Un objeto Android global pasado a Python.
- **Es:** Un canal de paso de mensajes/comandos estructurados.
```text
Python Skill
   ↓ { action: "set_alarm", payload: { time: "07:00", label: "gym" } }
Android Bridge (JSON/Protobuf over IPC/JNI)
   ↓
Kotlin Router
   ↓
AlarmManager
```
- La comunicación debe soportar operaciones asíncronas, callbacks de éxito/error y timeouts.

## 10. Audio Architecture
- **Origen:** Micrófono Android (AudioRecord).
- **Procesamiento continuo:** Se ejecuta en Kotlin dentro de un Foreground Service para evitar que Android mate el proceso y para optimizar batería. Python no debe mantener un hilo infinito escuchando bytes en bruto a través del JNI.

## 11. STT
**ARCHITECTURAL DECISION PENDING**
- *Opciones:* Whisper.cpp, Faster-Whisper, Modelos nativos de Android (Google Speech Recognition offline), Silero.
- *Criterio:* Menor latencia, menor huella de RAM y CPU. Preferiblemente procesado en Kotlin (vía C++ bindings) enviando solo el `Transcript` (string) a Python.

## 12. Wake Word
**ARCHITECTURAL DECISION PENDING**
- *Opciones:* Porcupine, Snowboy (Kotlin/C++).
- *Criterio:* Consumo energético casi nulo. **DEBE ejecutarse en Kotlin/C++**. Mandar audio continuo a Python para detectar el Wake Word destruiría la batería.

## 13. VAD
Debería ejecutarse inmediatamente después del Wake Word en la capa nativa (Kotlin/C++) para aislar el chunk de voz y pasarlo al STT local.

## 14. TTS
La respuesta generada por Python viaja por el Android Bridge hacia Kotlin, donde se utiliza `Android TextToSpeech` nativo. No se deben usar APIs Cloud de TTS salvo configuración explícita.

## 15. NLU & 16. Router
- **NLU:** Limpia el transcript y extrae entidades mediante heurísticas deterministas.
- **Router:** Determina la intención y asigna la estrategia de resolución. Responde "¿Qué tipo de operación es esta?". Usa reglas estáticas, y solo usa el Classifier o el Local LLM en caso de fallo.

## 17. Planner
Responde "¿Qué pasos requiere?". Actúa solo cuando el Router dictamina un `WORKFLOW` o `AGENT` que implique más de una acción secuencial.

## 18. Dispatcher
Responde "¿Qué componente debe ejecutar esta tarea?".
Toma el `Task` generado y lo despacha al executor correspondiente en la `Mobile Execution Layer`.

## 19. Skills
Objetos de lógica de negocio en Python. Ensamblan el comando, lo validan con Pydantic y envían la petición al `Android Bridge`. **Las Skills nunca controlan la UI directamente.**

## 20. Mobile Execution Layer
Jerarquía estricta de ejecución (Executor):
1. **NativeExecutor:** Llamadas nativas mediante Android APIs (AlarmManager).
2. **ContentProviderExecutor:** Manipulación de bases de datos Android (Contacts, Calendar).
3. **IntentExecutor:** Envío de Android Intents o Deep Links (`vnd.youtube://`).
4. **AccessibilityExecutor (Portal):** Usar los servicios de accesibilidad para manipular componentes UI nativos.
5. **DroidRunExecutor:** Análisis visual puro de la pantalla y tapping X/Y comandado por LLM.

## 21. Portal
El Portal (`appwiz/droidrun`) existente se mantiene pero se readapta.
- Se debe aislar de la automatización visual y centrarse en usar las APIs de `AccessibilityService` de Android de forma determinista para inyectar texto o clicks cuando los Intents no basten.

## 22. DroidRun
Auditoría del código legacy (`mobilerun/`):
- `Agent/FastAgent`: **DEPRECATE** (Reemplazados por el nuevo Core).
- `CLI`: **ISOLATE** (Útil para debug en PC, irrelevante en la app Android).
- `Tools (UI)`: **ADAPT** (Se moverán a la Mobile Execution Layer como DroidRunExecutor).
DroidRun se convierte exclusivamente en el fallback visual final cuando todas las capas superiores fallan o la app carece de APIs.

## 23. LLM Gateway
Abstracción de proveedores IA. El LLM es un razonador opcional, sin acceso directo a Android. Su output siempre se tipa mediante Pydantic (Structured Output) y se envía al Router/Planner.

## 24. Security
Frontera estricta. El LLM jamás toca la API de Android directamente.
El flujo obliga a una validación:
`Task → Capability Check → Android Permission Check → Risk Evaluation (LOW, MEDIUM, HIGH, CRITICAL) → User Confirmation → Execution`.

## 25. Permissions & 26. Confirmation
- **Android Permission:** Resuelto en Kotlin. Si falta un permiso (ej. `READ_CONTACTS`), la tarea aborta y solicita el permiso vía UI.
- **User Confirmation:** Resuelto lógicamente. Operaciones `HIGH/CRITICAL` (enviar mensaje, comprar) detienen el flujo y envían un evento al Android Bridge para que Kotlin pida "Sí/No" por voz o pantalla.

## 27. State, 28. Memory & 29. Persistence
- **Ephemeral Runtime State (RAM):** Ejecución de Workflows, buffers de audio.
- **Conversation State (RAM):** Contexto inmediato (¿De qué vídeo estábamos hablando?).
- **User Preferences (SQLite):** Configuraciones (ej. App por defecto de música).
- **Persistent Memory (SQLite):** Agendamiento y tareas pendientes aplazadas.

## 30. Events
- **EventBus Python:** Se mantiene para comunicación intra-proceso en Python (desacoplar logging, telemetría).
- **Python-Kotlin:** No es un EventBus abierto. Se deben usar `Commands` (Petición síncrona/timeout) o `Callbacks` unidireccionales.

## 31. Error Handling
- **Fallo STT/NLU/Router:** Pide clarificación al usuario o falla silenciosamente sin llamar al LLM.
- **Fallo Android API:** Reintenta o devuelve error. No hace fallback a DroidRun a menos que esté expresamente programado.
- **Red offline:** Fallback instantáneo a lógica determinista/Local LLM. Si no se puede, informa error. Nunca intenta llegar a la red.

## 32. Cancellation
- **Flujo:** El usuario dice "Cancela". Esto genera un Intent prioritario.
- **Acción:** Si hay un Workflow, se aborta usando `asyncio.cancel()`. Si hay una orden en el Android Bridge, se anula. Si requiere confirmación, se marca como rechazada.

## 33. Offline Modes
- **FULL OFFLINE:** Resolución determinista o modelo local.
- **HYBRID / ONLINE:** El Router delega en Cloud LLM o el Dispatcher invoca a APIs web (ej. Spotify).
*Si internet falla, el sistema se degrada a FULL OFFLINE sin interrumpir las capas nativas.*

## 34. Observability
Toda petición se acompaña de un `trace_id`. El Python logger debe emitir las salidas que luego serán capturadas por Logcat en Android.

## 35. Testing
- **Python Unit Tests:** Prueban routers, extracciones y Skills (Mockeando el Android Bridge).
- **Android Unit Tests:** Prueban el Android Bridge y los Executors nativos (Mockeando a Python).
- **Integration/E2E Tests:** Corren sobre un dispositivo real o emulador enviando audio simulado a Kotlin.

## 36. Dependency Strategy
Se purgarán dependencias pesadas innecesarias en el entorno Android. LlamaIndex será mitigado o retirado progresivamente a favor de llamadas directas a APIs o SDKs más ligeros para disminuir el tamaño del APK.

## 37. Current State vs 38. Target State
- **Current:** Scripts en PC controlando un Android por ADB y delegando todo el flujo UI a modelos en la nube.
- **Target:** App Android ligera con Python embebido, manejando el hardware nativamente y usando IA local/nube como razonador final.

## 39. Migration Strategy
1. **NO IMPLEMENTAR NADA AÚN.**
2. Crear PoC de la tecnología de embebido Python (Chaquopy/JNI).
3. Construir el Android Bridge y la App Kotlin base.
4. Mover el módulo `core/` (NLU, Router, Contratos) a Android.
5. Deprecar DroidRun como núcleo y encapsularlo como DroidRunExecutor.

## 40. Architectural Decisions
- Python es el cerebro lógico, no el controlador del hardware.
- Android/Kotlin es el dueño del ciclo de vida y del hardware.
- Separación rígida entre Decisión (Router/Dispatcher) y Ejecución Física (Executors).
- Seguridad impuesta mediante validación estructurada y confirmaciones manuales.

## 41. Pending Decisions
- **ARCHITECTURAL DECISION PENDING:** Estrategia exacta del Python Runtime en Android.
- **ARCHITECTURAL DECISION PENDING:** Dónde procesar exactamente STT, VAD y Wake Word (se inclina por Kotlin/C++ por batería).
- **ARCHITECTURAL DECISION PENDING:** Mecanismo físico del Android Bridge (IPC vs JNI vs local socket).

## 42. Risks
- Desempeño y peso del APK al incluir Python.
- Bloqueo de la app por mala gestión del Lifecycle entre hilos de Android y el Event Loop de Python.
