# Knowledge Baseline & Preparación Arquitectónica

## 1. Resumen
Se busca construir un asistente de voz híbrido (offline-first, native-first) sobre una base de código existente (`mobilerun` / DroidRun). El problema que resuelve es que DroidRun actualmente es fuertemente dependiente de LLMs en la nube (usa `llama-index` extensivamente para planificar y ejecutar cualquier acción en UI). El comportamiento esperado es que la nueva arquitectura actúe como un escudo/gateway determinista: el comando pasa por STT, extracción de entidades deterministas y enrutamiento basado en reglas antes de tocar un modelo IA o recurrir a la automatización visual de DroidRun.

## 2. Suposiciones
- SUPOSICIÓN: DroidRun (`mobilerun/`) seguirá existiendo como librería dentro del repo, pero el entrypoint del sistema completo se moverá a un orquestador superior (aún por escribir) que implementará los contratos de `core/`.
- SUPOSICIÓN: Las librerías nativas o la integración directa con los Intents de Android se harán en capas que aún no existen en el código (`skills/`, `mobile/native/`).

## 3. Dudas
- **Duda:** ¿Cuál es el mecanismo planeado para la comunicación entre el core (Python/PC) y el dispositivo Android para el envío de Intents nativos directos (sin usar DroidRun UI automation)?
  - **Por qué importa:** Afecta directamente al principio `native-first`.
  - **Recomendación:** Crear un servicio Android (APK compañero) ligero que exponga un servidor TCP o HTTP para recibir comandos deterministas y ejecutar Intents/APIs nativas.
  - **Pregunta:** ¿Se contempla desarrollar una App Android (companion app) para ejecutar los native Intents, o todo pasará por ADB shell a través de `mobilerun`?
- **Duda:** ¿Cómo persistiremos la memoria y contexto?
  - **Por qué importa:** La arquitectura en `ARCHITECTURE.md` habla de SQLite y VectorDB para offline. No hay dependencias ni código implementado para ello actualmente.
  - **Pregunta:** ¿Debemos agregar dependencias de base de datos local (ej. SQLAlchemy / Chroma) en la próxima fase?

## 4. Contradicciones
- **Problema:** `mobilerun` está completamente acoplado a `llama-index` y realiza invocaciones a LLMs para decidir qué hacer (ManagerAgent / ExecutorAgent).
  - **Impacto:** Rompe la separación de responsabilidades y el principio "deterministic-first".
  - **Solución recomendada:** Mantener `mobilerun/agent` estrictamente como fallback (`ExecutionMode.AGENT`) en el `ClassifierRouter`.

## 5. Decisiones arquitectónicas pendientes
- 🔴 **BLOQUEANTE:** La integración con el micrófono del sistema anfitrión (PC) o del móvil para el pipeline de STT continuo no está definida. Necesitamos saber de dónde provendrá el stream de audio.
- 🟠 **IMPORTANTE:** Estrategia exacta de persistencia offline (SQLite o similar) para la memoria conversacional.

## 6. Contratos afectados
Los contratos base ya fueron creados en `core/contracts.py` (Intent, Task, Context, etc.). No se requiere alterarlos todavía.

## 7. Flujo propuesto
`Micrófono -> buffer -> SimpleEnergyVAD -> WhisperProvider (mock) -> TranscriptNormalizer -> EntityExtractor -> RuleBasedRouter -> DirectSkill / LLM Gateway -> MobileController (ADB/Native/DroidRun)`

## 8. Estrategia offline
- **Offline Total:** STT local, Extracción determinista de intenciones, Rule-based routing y ejecución de Skills Nativas deben funcionar sin red.
- **Requiere Red:** Cloud LLM Gateway, APIs como Spotify, y DroidRun agent fallback que dependa de visión+LLM.

## 9. Uso de IA
- **NO_AI:** VAD, Normalización, Extracción de entidades por heurística, Rule-based router.
- **LOCAL_MODEL (Mock):** Whisper para STT. Clasificación semántica de routing.
- **CLOUD_MODEL:** Fallback complejo en LLM Gateway y ejecución de DroidRun UI Automation.

## 10. Seguridad
- Los comandos generados por `ExecutionMode.AGENT` requerirán inyección en un sistema de permisos (aún no codificado).
- Se necesita una capa interceptora antes de llamar a `MobileController` que pida entrada de usuario si el `risk_level` de la Tool/Skill es `HIGH`.

## 11. Manejo de errores
- Si el LLM o DroidRun fallan, devolver un `ExecutionResult(status=FAILED, retryable=True)`.
- Si se pierde la conexión de red, rutear forzosamente a `LocalLLM`.

## 12. Casos límite
- STT devuelve un intent ambiguo ("apaga eso") -> El router debe pasar a `ExecutionMode.CLARIFICATION`.
- Ruido de fondo dispara el VAD -> Entidades vacías, se aborta flujo en el Router.

## 13. Testing
Requerido:
- Mocks para `mobilerun` Agents.
- Tests E2E desde un payload de audio `.wav` hasta la salida de `ExecutionResult`.

## 14. Criterios de aceptación
(Pendiente de requerimiento específico del usuario).

## 15. Plan de implementación
1. Definir cómo recibir audio real (Integración de PyAudio / Micro).
2. Desarrollar un skill mock directo (`Native-first`).
3. Integrar la llamada al skill desde el router.
4. Acoplar la ejecución final a DroidRun solo si el router escoge AGENT.

## 16. Bloqueantes
1. ¿El audio va a provenir de la PC donde corre el script o se enviará por red desde un dispositivo móvil?
2. ¿Debemos integrar SQLAlchemy/SQLite ahora para la memoria de contexto, o trabajamos in-memory por el momento?

¿Quieres que congelemos este Knowledge Baseline como contrato arquitectónico del proyecto?
