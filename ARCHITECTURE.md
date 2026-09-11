# Comprehensive System Architecture

This document serves as the foundational contract and detailed architectural blueprint for the Hybrid Voice Assistant project. The system is engineered to prioritize deterministic, fast, and secure native execution, utilizing Large Language Models (LLMs) strictly as advanced reasoners rather than universal application controllers.

---

## 1. System Philosophy & Core Directives
1. **LLM as Reasoner:** LLMs are expensive in latency, cost, and hallucination risk. They are only invoked when a task cannot be handled deterministically.
2. **Native First:** Interaction with the device must always attempt to use Native APIs, Intents, ADB, or Accessibility Services first.
3. **UI Automation Fallback:** The inherited `DroidRun` framework (UI tree analysis and visual automation) is relegated to the absolute bottom of the execution priority list. It is a fallback for apps lacking APIs.
4. **Security by Design:** All parameters are typed (`pydantic`), and all high-risk operations (e.g., sending messages, deleting data, purchases) require explicit user confirmation.

---

## 2. Core Flow & Data Lifecycle

The lifecycle of a user request follows a strict, multi-layered pipeline to ensure minimal latency and maximum safety.

### 2.1. Audio / STT Layer (The Entry Point)
**Components:** `Microphone`, `VAD (Voice Activity Detection)`, `STTProvider`
- **Wake Word & Buffering:** The system listens passively for a wake word (e.g., "Asistente"). Upon detection, it opens a short-term audio buffer.
- **VAD (Voice Activity Detection):** `core/audio/vad.py` monitors the buffer for speech energy. When speech stops, the segment is isolated to prevent infinite recording loops and background noise contamination.
- **STT (Speech-to-Text):** The isolated raw audio chunk is passed to the `STTProvider` (`providers/stt/whisper_provider.py`). The system is agnostic to the STT backend but favors local, fast implementations (like Faster-Whisper) to generate a structured `Transcript` object containing text, segments, timestamps, and locale.

### 2.2. Understanding Layer (NLU)
**Components:** `TranscriptNormalizer`, `EntityExtractor`, `Intent`
- **Normalization:** `core/nlu/normalization.py` receives the raw transcript and strips out meaningless filler, punctuation, and common dictation errors (e.g., "pon me" -> "ponme", removing "¡!") to create a clean, uniform string.
- **Entity Extraction:** `core/nlu/entity_extractor.py` scans the normalized text for deterministic entities (like times, relative dates, and command labels) using rigid regex heuristics. This transforms natural language into actionable parameters (e.g., "mañana a las siete" -> `{"date": "tomorrow", "time": "07:00"}`).
- **Intent Encapsulation:** The raw text, normalized text, and extracted entities are wrapped into a strictly typed `Intent` Pydantic model (`core/contracts.py`).

### 2.3. Router Layer (The Decision Engine)
**Components:** `RuleBasedRouter`, `ClassifierRouter`
The router determines the `ExecutionMode` (`DIRECT`, `WORKFLOW`, `AGENT`, `LLM`, `CLARIFICATION`, `REJECT`) for a given `Intent`.
1. **Rule-Based Router:** `core/router/rule_router.py` evaluates the intent against a rigid dictionary of known high-confidence intents (e.g., `create_alarm` -> `DIRECT`). If a match is found, routing is instantaneous and uses zero tokens.
2. **Classifier Router:** If rules fail or confidence is medium, `core/router/classifier_router.py` performs keyword clustering (and eventually semantic embeddings) to infer the category.
3. **LLM Fallback:** If both deterministic routers fail to understand the request, the system finally delegates routing to a fast, local LLM to reason about the user's goal.

### 2.4. Execution Layers
Tasks are transformed from Intents into actionable `Task` models and dispatched based on their `ExecutionMode`.

1. **Direct Skills (`ExecutionMode.DIRECT`)**
   - Mapped to rigidly defined `Skill` classes (e.g., Alarm, Calendar, System settings).
   - Executes instantaneously using native APIs.
   - Example: "Turn off WiFi" -> Maps directly to Android system intent.

2. **Workflow Engine (`ExecutionMode.WORKFLOW`)**
   - Used for known multi-step deterministic tasks.
   - Executes a declarative pipeline of tools (e.g., YouTube summary: `youtube.search` -> `youtube.get_transcript` -> `llm.summarize`).

3. **LLM Planner / Agent (`ExecutionMode.AGENT`)**
   - Invoked for vague, complex, or unknown multi-step tasks (e.g., "Find my August invoice in the banking app and summarize it").
   - The LLM acts as a planner, generating a series of `Tool` calls.
   - The Agent operates within a strict environment with bounded `max_steps` and timeout constraints to prevent runaway loops.

### 2.5. Mobile Execution Abstraction (The Executor)
**Components:** `MobileController`
The backend of the assistant never touches the phone screen directly. Instead, skills use a generalized `MobileController` interface.
- **Priority 1: Native API:** (e.g., `content://com.android.calendar`)
- **Priority 2: Android Intents / Deep Links:** (e.g., `vnd.youtube://`)
- **Priority 3: ADB / Accessibility:** Simulating native UI events securely.
- **Priority 4: DroidRun Adapter:** Used strictly when the app lacks all the above. DroidRun captures the UI tree, sends it to the LLM Gateway, and performs automated visual tapping.

---

## 3. Core Infrastructure & Support Modules

### 3.1. LLM Gateway (`providers/llm/`)
Provides a unified abstraction (`LLMProvider`) over models.
- **LocalLLM:** A local instance (e.g., Llama 3 via Ollama/llama.cpp) used for zero-cost semantic classification, summarization, and small reasoning tasks.
- **CloudLLM:** A large, high-capacity model (e.g., GPT-4o, Claude 3.5 Sonnet) used exclusively for complex reasoning, dynamic tool planning, or parsing convoluted visual UI trees via DroidRun.
- **Capabilities:** Generation, Streaming, Structured Output (JSON mode mapped to Pydantic schemas), and Embeddings.

### 3.2. Event System (`core/events.py`)
An asynchronous Publish/Subscribe bus (`EventBus`). It decouples system components. For instance, the STT provider publishes a `transcript_ready` event, which the Router subscribes to, allowing the system to update UI components or loggers without blocking the execution thread.

### 3.3. Observability (`core/tracing.py` & `core/logger.py`)
- **ExecutionTracer:** Every action generates a unique `trace_id`. The tracer records step latencies, token consumption, router decisions, and errors into a `TraceRecord`. This data is critical for moving tasks from the expensive LLM layer down to the deterministic Rule layer over time.
- **Structured Logging:** Standardized logging output via stdout/files to monitor application health in real-time.

### 3.4. Configuration (`core/config.py`)
A central `AppConfig` singleton driven by Pydantic and environment variables. It controls critical flags like `LLM_ROUTING_MODE` (e.g., `local_first`), `STT_PROVIDER`, timeout parameters, and regional locales.

### 3.5. Memory & Context (Upcoming)
- **Short-Term Context:** Maintains the state of the current conversation (active app, last recognized entity).
- **Long-Term Memory:** SQLite-backed storage for user preferences and persistent states (e.g., "My default music app is Spotify").
- **Vector Storage:** Future integration planned for embedding-based intent classification and semantic memory retrieval.
