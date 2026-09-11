# Hybrid Voice Assistant — Architectural Baseline Final

Este documento consolida la arquitectura definitiva del asistente de voz, basada en auditorías del código existente y correcciones arquitectónicas críticas.

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
│       │ Native API                                 │       │
│       │ ContentProvider                            │       │
│       │ Intent                                     │       │
│       │ Accessibility                              │       │
│       │ DroidRunExecutor                           │       │
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
VOICE
 ↓
Wake Word
 ↓
VAD
 ↓
STT
 ↓
Transcript
 ↓
NLU
 ↓
Intent
 ↓
Router (Decide si necesita IA)
 ↓
 ├── DIRECT ────────────────┐
 ├── WORKFLOW ──────────────┤
 ├── LOCAL_LLM ─────────────┤
 └── AGENT ─────────────────┘
                            ↓
                         Planner
                            ↓
                           Task
                            ↓
                    Capability Registry
                            ↓
                      Security Gate
                            ↓
                  Permission / Risk
                            ↓
                    Confirmation?
                       /        \
                     YES         NO
                      ↓           ↓
                 User OK      Dispatcher
                      ↓           ↓
                      └──────→ Dispatcher (Asigna componente Python a cargo)
                                  ↓
                              Executor (Skill prepara el comando)
                                  ↓
                         AndroidCommand
                                  ↓
                           Native Android (Capa Física)
                                  ↓
                          AndroidResult
                                  ↓
                         Task completion
                                  ↓
                                TTS
```

## 3. Capability Registry & Security
Centraliza las reglas de seguridad, evitando que Routers o Skills dupliquen validaciones. Cada capability declara sus límites:
- `required_android_permissions`
- `risk_level` (LOW, MEDIUM, HIGH, CRITICAL)
- `allowed_execution_modes`
- `allowed_executors`
- `requires_confirmation`
- `offline_capable`

Un LLM jamás genera comandos `shell` puros o toca coordenadas. Emite peticiones restringidas que cruzan el `Capability Registry` y el `Security Gate`.

## 4. DroidRun Limitado
El DroidRunExecutor es el último peldaño estricto:
`NativeExecutor -> IntentExecutor -> ContentProviderExecutor -> AccessibilityExecutor -> DroidRunExecutor`
Si la ejecución llega a DroidRun y tiene un riesgo `>= HIGH`, exige confirmación humana ineludible.

## 5. El Android Bridge
Se define **como un contrato abstracto**, no como tecnología.
Transportará estrictamente:
- `Python → AndroidCommand → Native Dispatcher`
- `Android → AndroidResult → Python`
- `Android → NativeEvent → Python`
- `Python → ConfirmationRequest → Android`
- `Android → ConfirmationResult → Python`

## 6. Runtime Ownership & Recovery Manager
Un *Foreground Service* no es garantía de vida perpetua.
```text
Android Process -> puede morir -> Python Runtime muere -> RAM perdida
```
El sistema incorporará un **Recovery Manager** apoyado en SQLite para determinar en el reinicio:
- ¿Qué tarea estaba en curso?
- ¿Qué comandos ya se enviaron al Bridge?
- ¿Cuáles pueden reintentarse de forma segura y cuáles requieren de nuevo confirmación del usuario?

## 7. Separación Router / LLM Gateway
- **Router:** Decide *SI* se necesita IA o si basta con reglas deterministas.
  - Sub-componentes: `RuleClassifier`, `IntentClassifier`, `LLMClassifier` (fallback de clasificación).
- **LLM Gateway:** Decide *QUÉ* modelo usar si se requiere IA.
  - Sub-componentes: `LocalLLM`, `CloudLLM`, `Provider adapters`.

---

# GO / NO-GO PARA IMPLEMENTACIÓN

**GO WITH POC:**
La arquitectura lógica está completamente auditada y congelada.
Antes de construir el producto completo o escribir la primera línea de código de negocio, **se deben ejecutar estrictamente los siguientes 4 PoCs bloqueantes**:

| PoC | Pregunta Bloqueante |
| --- | --- |
| **P1 — Python Runtime** | ¿Podemos ejecutar Python + asyncio + Pydantic + sqlite3 de forma estable en Android? (Chaquopy vs JNI vs Embebido) |
| **P2 — Bridge** | ¿Cuál es el transporte físico más robusto para los contratos Command/Result definidos? (Sockets vs JNI vs IPC) |
| **P3 — Wake/VAD/STT** | ¿Podemos mantener voz offline en español con latencia, RAM y batería aceptables en el OS nativo? |
| **P4 — Portal** | ¿Podemos inicializar y reutilizar el `AccessibilityService` de DroidRun sin ninguna dependencia de `adb shell`? |

Hasta que P1-P4 pasen exitosamente, la implementación del producto completo no comenzará.
