# ARCHITECTURE.md — mcp-telegram

Servidor MCP de **cuenta de usuario** de Telegram (MTProto vía Telethon), no de bot. Este repo es el canónico de la pareja con `pocharlies/mcp-telegram` (ver Decisiones y trampas).

## Clientes y versiones
- Un único servidor MCP por **stdio** (`server.py`, FastMCP). No hay cliente web, iOS ni API HTTP propia.
- Lo consumen agentes MCP lanzándolo como proceso hijo (el README documenta la integración con MCPorter). **No tiene ruta en AgentGateway:** ninguna ruta de `k8s-agentgateway-pocharlies/k8s/base/agentgateway-config.yaml` apunta a este repo. La ruta `/social` del gateway va a `mcp-sse.whatsapp-mcp.svc:3010` (repo `k8s-socialmedia-pocharlies`), que es otro código.
- Versión: sin etiquetas ni versión publicada; el único «versionado» son los commits de `main`.

## Dependencias en ambos sentidos
- **De qué depende:** la API MTProto de Telegram (credenciales de my.telegram.org: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`), un fichero de sesión local creado con `python auth.py`.
- **Quién depende de él:** ningún manifiesto de `~/k8s` lo referencia por nombre (medido con grep el 01-10-2026). El conector de Telegram que corre en producción es `k8s-socialmedia-pocharlies/connectors/telegram` y `connectors/telegram-sync`.
- Contratos: el repo no tiene `CONTRACTS.yaml` ni marcas `# CONTRACT:`. Las 14 herramientas MCP (`list_chats`, `read_messages`, `send_message`, `send_file`, `search_messages`, `forward_message`, `delete_message`, …) son su superficie y no se renombran sin versión nueva.

## Stack
- Python, `telethon>=1.42.0`, `mcp[cli]>=1.26.0` (FastMCP), `python-dotenv>=1.0.0` (`requirements.txt`). Sin framework web, sin base de datos.
- No se usa: Bot API, bases de datos, cola ni HTTP.

## Componentes compartidos
- Ninguno. `server.py` contiene los formateadores (`_format_entity`, `_format_message`) y las herramientas; `auth.py` hace el login interactivo único.
- El módulo de sincronización a base de datos **no está aquí**: vive en `k8s-socialmedia-pocharlies/connectors/telegram-sync/sync/`. No se copia de vuelta.

## Cómo se construye
- Un solo fichero de servidor; cada herramienta es una función `@mcp.tool()` async que obtiene el cliente con `get_client()` (singleton Telethon).
- Variables en `.env` (plantilla `.env.example`); la sesión (`session*`) no se commitea.
- Regla de reutilización: lo que sea sincronización, bridge o auto-respuesta va al conector de socialmedia, no a este servidor.

## Tests
- No hay tests en el repo. Cualquier cambio de lógica debe traer tests unitarios con el cliente Telethon simulado antes de fusionarse.

## CI/CD y despliegue
- `.github/workflows/duplicados.yml` (detector de copia, reusable de `k8s-gitops-pocharlies`) y `pr-review.yml` (review automática).
- No hay imagen, Dockerfile, release ni aplicación de ArgoCD. Se ejecuta con `run.sh` / `python server.py` en el host que lo use. Tronco: `main`.

## Decisiones y trampas
- Hay un duplicado personal, `pocharlies/mcp-telegram` (2 commits, 2026-03-21, con `sync/`, `qr_auth.py` y `TELEGRAM_SESSION_STRING`). Veredicto de SC-1430: este repo es el canónico; se propone archivar el personal (no se archiva en esa épica).
- Se propone, aparte, valorar archivar también este repo con un puntero a `k8s-socialmedia-pocharlies/connectors/telegram`, que es lo que corre.
- Una sesión de usuario de Telegram equivale a la cuenta entera: nunca commitear `*.session` ni `TELEGRAM_SESSION_STRING`.

## Reutilización
- Antes de añadir funcionalidad de Telegram: comprobar `k8s-socialmedia-pocharlies/connectors/telegram` y `telegram-sync` y el MCP `/social` del gateway.
- Búsquedas hechas para este documento: `grep -rn "mcp-telegram"` en `~/k8s` (0 referencias en manifiestos), lectura de `server.py` y `requirements.txt`, comparación con `pocharlies/mcp-telegram`.
