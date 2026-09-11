# Project Audit - DroidRun Fork

## 1. Arquitectura actual
El proyecto actual (`mobilerun`) es un framework de agentes para controlar dispositivos móviles mediante LLMs.
Está estructurado principalmente en torno a la librería `llama-index` y `mobilerun-core-local`.

### Entry points
- CLI: `mobilerun/cli/main.py`
- Main package: `mobilerun/__init__.py` y `mobilerun/__main__.py`

### Dependencias Principales
- `llama-index` y extensiones (workflows, llms)
- `async_adbutils` para comunicación con Android via ADB
- `mobilerun-sdk` y `mobilerun-core-local`
- `pydantic`, `httpx`, `asyncio`

### Módulos
- `agent/`: Implementación de los agentes basados en LLM, ejecutores (executor), proveedores de modelos, trayectoria, utilidades.
- `tools/`: Sistema de herramientas que los agentes pueden utilizar (ui, ios, driver, etc).
- `cli/`: Interfaz de línea de comandos.
- `config/`: Manejo de configuraciones de usuario y agentes.
- `mcp/`: Protocolo de control de modelos.
- `telemetry/`: Posthog y Arize Phoenix.

### API pública
El SDK expone agentes (FastAgent, etc.), herramientas para interactuar con la UI, y clientes de configuración.

### CLI
Permite interactuar con el dispositivo mediante comandos como ejecutar flujos, configurar credenciales, e inicializar dispositivos.

### Sistema de herramientas
Ubicado en `mobilerun/tools/`. Permite interactuar con la interfaz gráfica mediante filtros, formatters y UI interaction.

### Sistema de agentes
Ubicado en `mobilerun/agent/`. Implementa ActionContext, ActionResult, Executors, y gestores de flujo.

### Comunicación con Android e iOS
Se utiliza ADB (`async_adbutils`) y un componente nativo (`mobilerun_core_local.driver.android.portal` / `ios`). Usa un portal (APK) instalado en el dispositivo y servicios de accesibilidad.

### UI Tree y Screenshots
Extraídos mediante el portal / servicios de accesibilidad instalados en el dispositivo (mobilerun_core_local).

### Manejo de errores
Manejo de excepciones en executors y tools, devolviendo ActionResults con detalles.

### Tests
Pruebas ubicadas en `tests/` y `agent-test-flows/`.

---

## 2. Identificación de Componentes

### KEEP
- Configuración de conexión con dispositivos (`async_adbutils`).
- Componentes base de interacción de UI (portal / accesibilidad) en `mobilerun-core-local`.
- Sistema de CLI (base para la nueva CLI).

### MODIFY
- `mobilerun/agent/`: Adaptar para que sirva solo como fallback (Agentic Fallback) en lugar del orquestador principal.
- `mobilerun/tools/`: Mapear a las nuevas interfaces de "Skills" y "Tools" cuando se requiera automatización UI.

### WRAP
- La interacción de UI actual (DroidRun) debe ser encapsulada dentro de `MobileController` (`mobile/droidrun/`).

### REPLACE
- El router principal. LLM ya no es el controlador universal, sino que se introduce un router híbrido (Direct, Workflow, Agent).
- Reemplazar el inicio directo del agente por el pipeline: Mic -> Whisper -> Intent -> Router.

### DO NOT TOUCH
- Archivos de lock de dependencias a menos que sea necesario.
- Core interno de comunicación de bajo nivel (`mobilerun_core_local` dependencias).

---

## 3. Definition of Done Checklist

- [x] Diagrama de arquitectura (En README.md / ARCHITECTURE.md).
- [x] Mapa de dependencias (Revisado pyproject.toml).
- [x] Lista de entry points (mobilerun/cli, __main__.py).
- [x] Lista de APIs (Agent, Tools, ActionContext).
- [x] Lista de módulos reutilizables (ADB, CLI, Portal connection).
- [x] Lista de deuda técnica (Dependencia fuerte del LLM para tareas simples).
- [x] Riesgos conocidos (Latencia de red, fallos del LLM en UI complex).
- [x] Estrategia de integración (Construir capas superiores: Audio, STT, NLU, Router, y usar mobilerun como fallback).
