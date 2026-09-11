# Architecture

The system is a local/hybrid voice assistant that uses LLMs as a reasoner, not as a universal phone controller.

## Core Flow
1. **Audio / STT Layer:** Microphone -> VAD -> Speech Capture -> Whisper -> Text
2. **Understanding Layer:** Normalization -> Entity Extraction -> Intent Classification -> Confidence
3. **Router:** Deterministic? -> Workflow? -> LLM? -> Agent?
4. **Execution Layers:**
   - Direct Skills
   - Workflow Engine
   - LLM Planner / Agent
5. **Tool Layer:** Alarms, Calendar, YouTube, Spotify, etc.
6. **Mobile Execution:** Native API, Intents, Accessibility, ADB, DroidRun

## Component Rules
- **DroidRun / UI Automation:** Used only as a fallback when native APIs are not available.
- **LLM:** Used only when reasoning is required or for complex multi-step workflows.

## Contracts & Core Modules Developed
- **Contracts (`core/contracts.py`):** `Intent`, `Task`, `Skill`, `Tool`, `ExecutionResult`, `Context`.
- **Event System (`core/events.py`):** Async publish/subscribe bus.
- **Config & Tracing (`core/config.py`, `core/logger.py`, `core/tracing.py`):** Observability and environment routing configurations.
- **Audio Pipeline (`core/stt/`, `core/audio/`):** VAD and STT provider abstractions (with mock Whisper fallback).
- **Routing & NLU (`core/router/`, `core/nlu/`):** Normalization, Entity extraction, Rule-based routing, and Classifier routing.
- **LLM Gateway (`providers/llm/`):** Abstractions and mock implementations for `LocalLLM` and `CloudLLM` supporting `generate`, `stream`, `structured_output`, and `embeddings`.
*(Potential Future Improvement: Hook up real embedding stores or vector databases for memory and intent classification).*
