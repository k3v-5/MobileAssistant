# Hybrid Voice Assistant — Architectural Baseline FINAL

```text
ARCHITECTURAL BASELINE: FINAL
STATUS: FROZEN
IMPLEMENTATION: BLOCKED BY P1-P4
LEGACY SOURCE: mobilerun / droidrun
PRODUCT RUNTIME: Android
DOMAIN CORE: Python
NATIVE HOST: Kotlin
LLM: Optional
DroidRun: Last-resort Executor
ADB: Development only
LlamaIndex: Deprecated / Removed
```

**PRINCIPIO RECTOR:**
> No estamos "convirtiendo DroidRun en un asistente". Estamos construyendo un asistente Android nuevo que reutiliza DroidRun como una capacidad de último recurso.

---

## 1. Physical Architecture & Domain Isolation
El asistente vive en Android. Python no es el dueño del core móvil, sino exclusivamente el **Domain/Decision Core**.

```text
                         ANDROID DEVICE
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Android Native Runtime                                    │
│                                                            │
│  Foreground Service                                        │
│       │                                                    │
│       ├── Microphone                                       │
│       ├── Wake Word                                        │
│       ├── VAD                                              │
│       ├── STT                                              │
│       └── TTS                                              │
│                                                            │
│              ↓ Transcript                                  │
│                                                            │
│       ┌──────────────────────────────┐                     │
│       │      ANDROID BRIDGE          │                     │
│       │ Command / Result / Events    │                     │
│       └──────────────┬───────────────┘                     │
│                      ↕                                     │
│       ┌──────────────────────────────┐                     │
│       │       PYTHON CORE            │                     │
│       │ (Domain / Decision Core)     │                     │
│       │                              │                     │
│       │ NLU                          │                     │
│       │   ↓                          │                     │
│       │ Intent                       │                     │
│       │   ↓                          │                     │
│       │ Router                       │                     │
│       │   ↓                          │                     │
│       │ Planner                      │                     │
│       │   ↓                          │                     │
│       │ Security Gate                │                     │
│       │   ↓                          │                     │
│       │ Dispatcher                   │                     │
│       │   ↓                          │                     │
│       │ Skills                       │                     │
│       │                              │                     │
│       │ LLM Gateway ── Local/Cloud   │                     │
│       └──────────────┬───────────────┘                     │
│                      │                                     │
│                      ↓ AndroidCommand                      │
│                                                            │
│       ┌────────────────────────────────────────────┐       │
│       │          NATIVE EXECUTION LAYER            │       │
│       │                                            │       │
│       │ Native Dispatcher                          │       │
│       │   ├── NativeExecutor                       │       │
│       │   ├── ContentProviderExecutor              │       │
│       │   ├── IntentExecutor                       │       │
│       │   └── AccessibilityExecutor                │       │
│       │         └── DroidRunExecutor               │       │
│       └────────────────────────────────────────────┘       │
│                                                            │
│       SQLite                                               │
│       ├── Preferences                                      │
│       ├── Tasks                                            │
│       ├── Recovery state                                   │
│       └── Audit                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 2. Flujo Definitivo de Peticiones
La palabra `deterministic` describe la estrategia en la toma de decisión (Router/Planner), no la capa física de ejecución.

```text
┌─────────────────────────────────────────────────────┐
│                    USER VOICE                       │
└──────────────────────┬──────────────────────────────┘
                       ↓
                 Native Audio
                       ↓
              Wake Word / VAD
                       ↓
                     STT
                       ↓
                  Transcript
                       ↓
                Python NLU
                       ↓
                    Intent
                       ↓
                   Router
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
    DIRECT          WORKFLOW          AGENT
       │               │                │
       │            Planner          Planner
       │               │                │
       └───────────────┼────────────────┘
                       ↓
                      Task
                       ↓
              Capability Registry
                       ↓
                 Security Gate
                       ↓
              Permission / Risk
                       ↓
                Confirmation
                       ↓
                  Dispatcher
                       ↓
                    Skill
                       ↓
                AndroidCommand
                       ↓
             Native Dispatcher
                       ↓
              ┌────────┴─────────┐
              ↓                  ↓
        Native Executor    Accessibility
              ↓                  ↓
         Android APIs       Portal
                                 ↓
                         DroidRunExecutor
                         (LAST RESORT)
              └────────┬─────────┘
                       ↓
                 AndroidResult
                       ↓
                Recovery Manager
                       ↓
                  Task State
                       ↓
                      TTS
```

## 3. Rol del LLM (Razonador Opcional)
El LLM Gateway no es el centro del sistema; es un proveedor de razonamiento al que el sistema recurre únicamente cuando se necesita IA.
```text
Router
  │
  └── necesita IA
          ↓
      LLM Gateway
       ├── LocalLLM
       └── CloudLLM
          ↓
   Structured Output
          ↓
       Validation
          ↓
       Task / Intent
          ↓
   Security Gate
```

## 4. Security & Capability Registry
Centraliza las reglas de seguridad, evitando que Routers o Skills dupliquen validaciones. Cada capability declara sus límites:
- `required_android_permissions`
- `risk_level` (LOW, MEDIUM, HIGH, CRITICAL)
- `allowed_execution_modes`
- `allowed_executors`
- `requires_confirmation`
- `offline_capable`

Un LLM jamás genera comandos `shell` puros o toca coordenadas. Emite peticiones restringidas que cruzan el `Capability Registry` y el `Security Gate`.

## 5. El Android Bridge
Se define **como un contrato abstracto**, no como tecnología de transporte.
Transportará estrictamente:
- `Python → AndroidCommand → Native Dispatcher`
- `Android → AndroidResult → Python`
- `Python → ConfirmationRequest → Android`
- `Android → ConfirmationResult → Python`

**NativeEvent Classifier:**
No es un EventBus genérico, sino un tipado fuerte de eventos específicos:
```text
NativeEvent
 ├── PROCESS_STATE_CHANGED
 ├── AUDIO_STATE_CHANGED
 ├── PERMISSION_CHANGED
 ├── ACCESSIBILITY_STATE_CHANGED
 ├── CONFIRMATION_RESULT
 └── EXECUTION_INTERRUPTED
```

## 6. Runtime Ownership & Recovery Manager
Un *Foreground Service* no es garantía de vida perpetua.
```text
Android Process -> puede morir -> Python Runtime muere -> RAM perdida
```
El sistema incorporará un **Recovery Manager** apoyado en SQLite para determinar en el reinicio:
- ¿Qué tarea estaba en curso?
- ¿Qué comandos ya se enviaron al Bridge?

**Toda operación recuperable debe definir explícitamente su política de idempotencia, retry y recovery.**
Se utilizarán identificadores para evitar ejecución múltiple (e.g. envíos dobles de SMS o compras duplicadas):
```text
Task ID:       task_123
Command ID:    cmd_456
Idempotency:   idem_789
```

## 7. Separación Router / LLM Gateway
- **Router:** Decide *SI* se necesita IA o si basta con reglas deterministas.
  - Sub-componentes: `RuleClassifier`, `IntentClassifier`, `LLMClassifier` (fallback de clasificación).
- **LLM Gateway:** Decide *QUÉ* modelo usar si se requiere IA.
  - Sub-componentes: `LocalLLM`, `CloudLLM`, `Provider adapters`.

## 8. Separation of Dispatching and Execution
- **Skill:** La Skill abstracta (en Python) prepara la intención y genera el `AndroidCommand`.
- **Native Dispatcher:** Recibe el comando estructurado y lo enruta al Executor correspondiente dentro de Android.
- **Executor:** Ejecuta físicamente la acción (`NativeExecutor`, `IntentExecutor`, etc.).

---

# GO / NO-GO PARA IMPLEMENTACIÓN

**IMPLEMENTATION BLOCKED BY P1-P4**

Antes de construir el producto completo o escribir la primera línea de código de negocio, **se deben ejecutar estrictamente los siguientes 4 PoCs bloqueantes**:

| PoC | Pregunta Bloqueante |
| --- | --- |
| **P1 — Python Runtime** | ¿Podemos ejecutar Python + asyncio + Pydantic + sqlite3 de forma estable en Android? (Chaquopy vs JNI vs Embebido) |
| **P2 — Bridge** | ¿Cuál es el transporte físico más robusto para los contratos Command/Result definidos? (Sockets vs JNI vs IPC) |
| **P3 — Wake/VAD/STT** | ¿Podemos mantener voz offline en español con latencia, RAM y batería aceptables en el OS nativo? |
| **P4 — Portal** | ¿Podemos inicializar y reutilizar el `AccessibilityService` de DroidRun **sin ninguna dependencia de ADB**, en background, manteniendo acceso seguro y recuperación ante caídas? |

*El desarrollo final de la arquitectura iniciará transformando las conclusiones de estos PoCs en ADRs definitivos.*
