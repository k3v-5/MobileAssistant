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

## Contracts
Definitions for fundamental domain models are detailed in `core/contracts.py` (or equivalent documentation). This includes:
- `Intent`
- `Task`
- `Skill`
- `Tool`
- `ExecutionResult`
- `Context`
