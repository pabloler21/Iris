# ClawNest — Plan Técnico MVP (v3)
### Documento de instrucciones para implementación multi-agente
### Compatible con Claude Code, OpenCode, Codex, Cursor, y otros
### Objetivo: agente AI personal con Job Tracker funcionando en una semana

---

## Setup multi-agente: Claude Code + OpenCode/Kimi K2

Este proyecto está diseñado para ser trabajado con **múltiples agentes AI**
intercambiables a lo largo del desarrollo. La realidad de un developer en 2026
es que distintas tareas se hacen mejor con distintos agentes. Este plan asume
que vas a alternar entre al menos dos:

**Claude Code:**
- Para tareas que requieren mayor capacidad de razonamiento
- Configuración inicial compleja, debugging difícil
- Code review de cosas importantes
- Cuando necesitás máxima calidad y podés pagar el costo

**OpenCode con Kimi K2 vía OpenRouter:**
- Para tareas de implementación rutinaria
- Generación de boilerplate (Pydantic models, scaffolding de FastAPI)
- Refactoring mecánico
- Cuando querés ahorrar créditos

Otros agentes compatibles (futuro): Codex CLI, Cursor, Gemini CLI, Windsurf.

## Cómo se mantiene el contexto entre agentes

La clave para que esto funcione sin caos es el sistema de archivos de contexto:

### AGENTS.md — archivo principal (todos los agentes lo leen)

Vive en la raíz del repo. Es el "constitución" del proyecto. Contiene stack,
convenciones, reglas no negociables, contexto del usuario.

Es leído nativamente por: OpenCode, Codex CLI, Cursor, Gemini CLI, Windsurf,
Continue, Amp, Warp, Goose, y otros.

### CLAUDE.md — symlink a AGENTS.md (solo para Claude Code)

Claude Code (a la fecha) no lee AGENTS.md nativamente. Lee CLAUDE.md. Para
evitar mantener dos archivos, se crea un symlink desde el primer día:

```bash
ln -s AGENTS.md CLAUDE.md
```

Esto hace que Claude Code lea el mismo archivo que los demás agentes. Un archivo,
una fuente de verdad, cero duplicación.

### notes/ — handoff notes (cualquier agente puede leer/escribir)

Carpeta con archivos `handoff-fase-X.md`. Cada agente, al terminar una sesión,
genera o actualiza el handoff note de la fase actual.

### decisions/ — ADRs (cualquier agente puede leer/escribir)

Carpeta con archivos `NNN-titulo.md`. Cada decisión arquitectónica se documenta
una vez, queda disponible para cualquier agente futuro.

## Regla obligatoria — actualización al terminar tareas

Esto es CRÍTICO para que el sistema funcione con múltiples agentes:

**Al terminar cualquier tarea significativa, el agente DEBE:**
1. Actualizar el handoff note de la fase actual con lo que se completó
2. Crear ADR si hubo una decisión arquitectónica importante
3. Actualizar el README si cambió algo visible del proyecto
4. Confirmar al usuario que el contexto fue actualizado

**Definición de "tarea significativa":**
- Completar un paso del plan
- Tomar una decisión técnica
- Resolver un bug que llevó tiempo
- Cualquier cosa que un agente futuro necesite saber

**Si el agente termina sin actualizar el contexto, el sistema se rompe.** El
próximo agente va a empezar sin saber qué pasó. Por eso esta regla es
no-negociable.

---

## Cómo usar este documento

**Reglas para CUALQUIER IA implementadora (Claude Code, OpenCode, Codex, etc.):**

- Generar código solo cuando se solicite explícitamente
- Explicar decisiones técnicas cuando se generen
- Preguntar antes de tomar decisiones de diseño que no estén especificadas
- Comentar el código en español, código en inglés (preferencia de Pablo)
- Errores y debugging: explicar la causa antes de la solución
- Si un paso depende de credenciales o configuración del usuario, pausar y solicitarla
- **OBLIGATORIO: actualizar handoff note y/o ADRs al terminar cada tarea**

**Contexto del usuario:**
- AI Engineer Jr en Buenos Aires, transición desde data analytics
- Stack conocido: Python, FastAPI, LangChain, Pydantic, Streamlit
- Hardware servidor: Linux Mint, 16GB RAM, CPU mala, sin GPU
- Trabaja desde compu principal Windows 10 + WSL2, SSH al servidor Linux
- Aprende mejor con explicaciones conceptuales antes del código
- Convenciones: código en inglés, comentarios en español, commits en inglés

---

## Contexto del proyecto

**Proyecto:** ClawNest — un asistente personal AI corriendo 24/7 en un homelab
Linux, accesible por Telegram desde cualquier lugar del mundo.

**Stack tecnológico:**
- **OpenClaw** — framework base del agente (corre en el Linux Mint)
- **Kimi K2 vía OpenRouter** — cerebro LLM del agente ClawNest
- **Telegram Bot API** — interfaz de usuario
- **Tailscale + Tailscale Funnel** — conectividad y exposición pública
- **Docker** — containerización de servicios auxiliares
- **Qdrant** — vector database para memoria extendida
- **Nginx** — reverse proxy para múltiples servicios
- **FastAPI** — para skills custom complejas

**Importante — distinguir dos cosas que se confunden:**
- "Kimi K2" como cerebro de **ClawNest** (el agente que estás construyendo)
- "Kimi K2 vía OpenCode" como **herramienta de desarrollo** (uno de los agentes
  que vos usás para construir ClawNest)

Son usos distintos del mismo modelo. Una API key sirve para ambos casos.

**Skill estrella del MVP:** Job Tracker — busca ofertas de AI Engineer en
LinkedIn, Get on Board, Workana, RemoteOK y We Work Remotely. Filtra por
keywords relevantes y notifica por Telegram.

**Restricciones de hardware del servidor:**
- 16GB RAM, sin GPU, CPU limitada
- No correr modelos LLM localmente — usar siempre API externa
- Minimizar contenedores Docker simultáneos
- Embeddings: usar modelo liviano local (all-MiniLM-L6-v2)

**Setup físico de trabajo:**
- Compu principal Windows 10 + WSL2: donde corre el agente de desarrollo
  (Claude Code u OpenCode/Kimi)
- Compu servidor Linux Mint: donde corre ClawNest una vez deployado
- Conexión entre las dos: SSH vía Tailscale después de la Fase 1

---

# FASE 0 — Setup de contexto del proyecto
### Duración estimada: 1 hora
### Dónde se trabaja: compu principal (Windows + WSL2)
### Agente recomendado: Claude Code (mejor para setup inicial)
### Entregable: repo en GitHub con AGENTS.md + estructura de carpetas

## Qué se construye en esta fase

Antes de cualquier código de proyecto, configuramos el sistema de contexto.
Esto permite que cada sesión futura (con cualquier agente) arranque con la
info correcta sin re-explicar todo.

## Pasos a ejecutar

### Paso 0.1: Crear el repo en GitHub

Pasos manuales del usuario:
- Ir a github.com
- Crear repo público llamado `clawnest`
- NO inicializar con README (vamos a crear uno nosotros)
- Anotar la URL del repo

### Paso 0.2: Setup local en compu principal

En WSL2 (terminal Linux dentro de Windows):

```bash
mkdir -p ~/projects/clawnest
cd ~/projects/clawnest
git init
git remote add origin https://github.com/[usuario]/clawnest.git
```

### Paso 0.3: Crear AGENTS.md

Crear archivo `AGENTS.md` en la raíz del proyecto con este contenido:

```markdown
# ClawNest

Personal AI assistant running 24/7 on Linux homelab, accessible via Telegram.
Portfolio piece for AI Engineer Jr job search by Pablo (Buenos Aires).

## Stack
- Runtime: Python 3.11 (services), Node.js 20+ (OpenClaw)
- LLM: Kimi K2 via OpenRouter (model: moonshotai/kimi-k2)
- Agent framework: OpenClaw (hackable install method)
- Memory: Qdrant via Docker
- API services: FastAPI + Pydantic v2
- Reverse proxy: Nginx in Docker
- Network: Tailscale + Funnel
- OS: Linux Mint (homelab), Windows + WSL2 (dev)

## Build & Run
```bash
# Start all services on homelab
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f [service_name]

# OpenClaw runs as systemd service (NOT in Docker)
sudo systemctl status clawnest
journalctl -u clawnest -f
```

## Code conventions
- Python: ruff for lint, black for format, type hints required
- Code in English, comments in Spanish
- Commit messages in English, conventional commits format
- Async by default for I/O operations
- All Pydantic models in `models/` directories

## Architecture rules
- No LLM inference locally (use OpenRouter)
- Custom skills as separate FastAPI services in Docker
- OpenClaw runs on host, NOT in Docker (needs system access)
- All secrets in .env (never commit, gitignored)
- One service per docker-compose service

## Multi-agent workflow rules
This project is worked on with multiple AI agents (Claude Code, OpenCode/Kimi,
others). To keep context coherent across agents:
- CLAUDE.md is a symlink to this file (`ln -s AGENTS.md CLAUDE.md`)
- At the end of EVERY task, update `notes/handoff-fase-X.md`
- Create ADR in `decisions/NNN-title.md` for any architectural decision
- Update README when project status changes visibly
- Never end a session without updating context files

## Workflow
- One phase per session, max 4hs of work
- Read latest handoff note at start of session
- Always generate/update handoff note at end of session
- Update README per phase completed
- Architecture decisions documented in `decisions/NNN-title.md`

## Hard rules — never break
- Never commit .env, API keys, or tokens
- Never modify production homelab without testing locally first
- Never delete data without explicit user confirmation
- Never modify systemd services without backing up first

## User context (Pablo)
- AI Engineer Jr, transitioning from data analytics
- Strong: Python, FastAPI, LangChain, Pydantic
- Learning: Docker, Nginx, Tailscale, vector DBs
- Hardware homelab: Linux Mint, 16GB RAM, no GPU
- Dev machine: Windows 10 + WSL2
- Learning style: explain concepts before code
- Prefer Socratic questioning when learning new things
- Spanish (Rioplatense), B2 English

## Key directories
- `backend/src/` — Python services source
- `skills/` — Custom OpenClaw skills
- `notes/` — Handoff notes between sessions (READ ON SESSION START)
- `decisions/` — Architecture Decision Records (ADRs)
- `nginx/` — Reverse proxy config

## When in doubt
- Read latest handoff note in `notes/`
- Check `decisions/` for past architectural choices
- Ask before changing existing patterns
```

### Paso 0.4: Crear symlink CLAUDE.md → AGENTS.md

Para que Claude Code lea el mismo archivo:

```bash
ln -s AGENTS.md CLAUDE.md
```

Verificar: `ls -la CLAUDE.md` debería mostrar `CLAUDE.md -> AGENTS.md`

### Paso 0.5: Crear estructura de carpetas

```bash
mkdir -p notes
mkdir -p decisions
mkdir -p backend/src
mkdir -p skills
mkdir -p nginx
```

### Paso 0.6: Crear .gitignore

```
.env
__pycache__/
*.pyc
.venv/
venv/
node_modules/
data/
*.log
.DS_Store
CLAUDE.local.md
```

Nota: el symlink CLAUDE.md SÍ se commitea (es un archivo de configuración). El
que se ignora es CLAUDE.local.md (para overrides personales).

### Paso 0.7: Crear README.md inicial

```markdown
# ClawNest

Personal AI assistant running on Linux homelab.

## Status
Currently in development — Fase 0 completed.

## Documentation
- [Project context for AI agents](AGENTS.md)
- [Architecture decisions](decisions/)
- [Session handoff notes](notes/)

## Multi-agent compatibility
This project is built using multiple AI coding agents.
CLAUDE.md is symlinked to AGENTS.md for unified context across all tools.
```

### Paso 0.8: Crear primer handoff note

Archivo `notes/handoff-fase-0.md`:

```markdown
# Handoff: Fase 0 - Setup de contexto

## Completed
- Initial repo structure
- AGENTS.md with project constitution
- CLAUDE.md symlinked to AGENTS.md (multi-agent compat)
- Folder structure for notes/, decisions/, backend/, skills/, nginx/
- .gitignore with security defaults
- Initial README.md

## Decisions made
- Using AGENTS.md as primary context file (cross-tool standard)
- Symlinking CLAUDE.md to AGENTS.md for Claude Code support
- Notes folder for session handoffs (read at start, update at end)
- Decisions folder for ADRs

## Files modified
- AGENTS.md (created)
- CLAUDE.md (symlink to AGENTS.md)
- .gitignore (created)
- README.md (created)

## Pending
- None — ready to start Fase 1

## Bugs / issues
- None

## Next session: Fase 1 (Preparación del homelab)
Read AGENTS.md first, then this note, then proceed with Fase 1 steps from the
plan. Fase 1 requires physical access to the Linux Mint computer (no SSH yet).

## Notes for next agent
The CLAUDE.md symlink works on Linux/WSL2/Mac. On native Windows it requires
admin permissions to create symlinks. Verify with `ls -la CLAUDE.md`.
```

### Paso 0.9: Crear template de ADR

Archivo `decisions/000-template.md`:

```markdown
# ADR NNN: Title

## Context
What's the situation that requires a decision?

## Options considered
- Option 1: pros and cons
- Option 2: pros and cons
- Option 3: pros and cons

## Decision
What we chose.

## Justification
Why we chose it.

## Consequences
What we gain and what we accept as tradeoff.

## Date
YYYY-MM-DD

## Author
Pablo + [agent name, e.g., Claude Code or OpenCode/Kimi]
```

### Paso 0.10: Primer ADR sobre el setup multi-agente

Archivo `decisions/001-multi-agent-context.md`:

```markdown
# ADR 001: Multi-agent context management with AGENTS.md + CLAUDE.md symlink

## Context
This project will be developed using multiple AI coding agents (Claude Code,
OpenCode with Kimi K2, possibly Codex/Cursor in the future). Each agent needs
project context to be effective, but maintaining duplicate context files would
cause drift.

## Options considered
- Maintain separate CLAUDE.md and AGENTS.md: high risk of drift
- Use only CLAUDE.md: would break OpenCode and other non-Claude agents
- Use only AGENTS.md: Claude Code doesn't read it natively
- Symlink CLAUDE.md → AGENTS.md: single source of truth, both agents work

## Decision
Use AGENTS.md as primary context file, create symlink CLAUDE.md → AGENTS.md.

## Justification
- AGENTS.md is the Linux Foundation-backed open standard for 2026
- Most modern coding agents support it natively
- Symlink solves Claude Code's lack of native AGENTS.md support
- Single file to maintain, zero drift risk
- Future-proof: when Claude Code adds AGENTS.md support, just delete the symlink

## Consequences
- Pro: One source of truth across all agents
- Pro: Easy to maintain
- Con: Symlinks require admin on native Windows (not an issue with WSL2)
- Con: Some legacy tools might not follow symlinks (none we use)

## Date
[YYYY-MM-DD del momento del setup]

## Author
Pablo + [agent que ejecutó la Fase 0]
```

### Paso 0.11: Primer commit y push

```bash
git add .
git commit -m "chore: initialize project structure and multi-agent context system"
git branch -M main
git push -u origin main
```

## Validaciones antes de pasar a Fase 1

- [ ] Repo creado en GitHub
- [ ] AGENTS.md existe en la raíz y tiene < 100 líneas
- [ ] CLAUDE.md existe como symlink a AGENTS.md
- [ ] Carpetas notes/, decisions/, backend/, skills/, nginx/ existen
- [ ] .gitignore protege secrets
- [ ] README.md inicial creado
- [ ] notes/handoff-fase-0.md creado
- [ ] decisions/000-template.md creado
- [ ] decisions/001-multi-agent-context.md creado
- [ ] Primer commit y push hechos al repo remoto

---

# Flujo de trabajo por sesión (cualquier agente)

A partir de la Fase 1, cada sesión sigue este patrón:

## Al inicio de cada sesión

1. **El agente carga AGENTS.md/CLAUDE.md automáticamente** (al abrir el agente
   desde la carpeta del proyecto)

2. **Pedirle al agente que lea el último handoff note:**
   ```
   "Leé notes/handoff-fase-X.md antes de empezar."
   ```

3. **Decirle qué vas a hacer hoy y qué agente sos (opcional pero útil):**
   ```
   "Hoy vamos por la Fase Y, paso Y.Z. Estoy usando [Claude Code / OpenCode con
   Kimi K2]. Procedé."
   ```

## Durante la sesión

- Trabajás normalmente
- Si surge una decisión arquitectónica importante, pedile al agente que cree
  un ADR en `decisions/NNN-titulo.md`
- Si el contexto empieza a saturarse:
  - En Claude Code: usá `/compact` con prompt custom
  - En OpenCode/otros: cerrá la sesión, abrí una nueva (esos no tienen compact)
- Si encontrás un bug y su solución, pedile al agente que lo anote para el
  handoff note

## Al final de cada sesión (CRÍTICO)

1. **Actualizar el handoff note:**
   ```
   "Actualizá notes/handoff-fase-X.md con todo lo que hicimos hoy. Si la fase
   está completa, marcala como completed. Si quedó a medias, anotá exactamente
   dónde quedamos."
   ```

2. **Crear ADRs si hubo decisiones:**
   ```
   "Si tomamos alguna decisión arquitectónica importante hoy, creá el ADR
   correspondiente en decisions/."
   ```

3. **Actualizar README si hubo progreso visible:**
   ```
   "Actualizá el README con el estado actual del proyecto."
   ```

4. **Commit y push:**
   ```bash
   git add .
   git commit -m "feat: complete fase X — [breve descripción]"
   git push
   ```

Si saltás cualquiera de estos pasos al final de la sesión, el próximo agente
va a empezar sin contexto y vas a perder tiempo.

---

# Asignación recomendada de agentes por fase

Esta es una guía, no es rígida. Adaptá según prefieras y según los créditos
que tengas disponibles.

| Fase | Tarea | Agente recomendado | Razón |
|------|-------|--------------------|----|
| 0 | Setup de contexto | Claude Code | Setup inicial, vale la pena calidad |
| 1 | SSH + Tailscale | OpenCode/Kimi | Comandos rutinarios de sistema |
| 2 | Docker + Qdrant | OpenCode/Kimi | docker-compose es boilerplate |
| 3 | OpenClaw setup | Claude Code | Configuración compleja, debugging |
| 4 | Telegram integration | OpenCode/Kimi | Integración relativamente directa |
| 5 | Memoria extendida | Claude Code | Diseño de arquitectura crítico |
| 6 | Job Tracker | Mixto: Claude Code para diseño, OpenCode/Kimi para scrapers | Tarea grande con partes distintas |
| 7 | Polish + deploy | Claude Code | Last mile, vale la pena calidad |

**Regla general:** usá Claude Code cuando la calidad importa mucho. Usá
OpenCode/Kimi cuando la tarea es mecánica.

---

# Contexto del proyecto

(Igual que antes — pego solo lo esencial para no duplicar)

**Stack tecnológico:**
- OpenClaw, Kimi K2 via OpenRouter, Telegram, Tailscale, Docker, Qdrant, Nginx, FastAPI

**Skill estrella del MVP:** Job Tracker — busca ofertas en LinkedIn, Get on
Board, Workana, RemoteOK, WeWorkRemotely. Filtra con LLM. Notifica por Telegram.

**Restricciones:** 16GB RAM sin GPU, no LLMs locales, embeddings con
all-MiniLM-L6-v2.

---

# FASE 1 — Preparación del homelab
### Duración estimada: 4 horas
### Dónde se trabaja: Linux Mint físicamente (no hay SSH todavía)
### Agente recomendado: OpenCode con Kimi K2
### Entregable: Linux Mint accesible por SSH vía Tailscale desde cualquier lado

## Notas especiales de esta fase

Esta es la única fase que requiere estar físicamente frente al Linux Mint con
teclado y monitor. Después de la Fase 1, todo se hace por SSH desde la compu
principal.

**Tu agente de desarrollo (Claude Code u OpenCode) corre en la compu principal,
NO en el Linux Mint.** El agente te genera los comandos, vos los ejecutás en
el Linux Mint físicamente. Una vez configurado SSH al final de la fase, en las
fases siguientes el agente puede ejecutar comandos en el Linux Mint vía SSH.

## Pasos a ejecutar

### Paso 1.1: Setup inicial del sistema

En el Linux Mint, directamente:
- Actualizar paquetes con apt update + upgrade
- Instalar herramientas básicas: curl, git, htop, ufw, nano
- Configurar hostname significativo (ej: "clawnest-homelab")
- Crear estructura de directorios en `/home/pablo/clawnest/` para el proyecto

### Paso 1.2: Configurar OpenSSH

- Instalar openssh-server
- Habilitar servicio para arranque automático
- Verificar que está escuchando en puerto 22

### Paso 1.3: Autenticación SSH por llaves

- Generar par de llaves ed25519 en la compu principal (WSL2)
- Configurar `authorized_keys` en el homelab
- Establecer permisos correctos (700 para .ssh, 600 para authorized_keys)
- Configurar `sshd_config` para deshabilitar:
  - PasswordAuthentication
  - PermitRootLogin
- Probar conexión SSH sin password desde compu principal
- Configurar alias SSH en compu principal (`~/.ssh/config`)

### Paso 1.4: Tailscale

- Crear cuenta en tailscale.com (paso manual del usuario)
- Instalar Tailscale en el homelab via script oficial
- Autenticar dispositivo
- Verificar conexión con `tailscale status`
- Habilitar Tailscale SSH (`sudo tailscale up --ssh`)
- Instalar Tailscale en compu principal del usuario
- Probar acceso desde compu principal vía Tailscale
- Configurar alias SSH actualizado con hostname Tailscale

### Paso 1.5: Configuración de laptop (si aplica)

Si el homelab es una laptop:
- Editar `/etc/systemd/logind.conf`
- Cambiar `HandleLidSwitch` a `ignore`
- Aplicar cambios

### Paso 1.6: Clonar el repo en el homelab

```bash
# En el homelab
cd /home/pablo/clawnest
git clone https://github.com/[usuario]/clawnest.git .
```

### Paso 1.7: Actualizaciones de contexto OBLIGATORIAS

Antes de cerrar la sesión:

1. Crear `decisions/002-tailscale-vs-cloudflare.md` documentando elección
2. Actualizar `notes/handoff-fase-1.md` con:
   - Lo que se completó
   - IPs del homelab (local y Tailscale)
   - Hostname Tailscale del homelab
   - Cualquier issue encontrado y cómo se resolvió
3. Actualizar README con el estado actual
4. Commit + push desde la compu principal

## Validaciones antes de pasar a Fase 2

- [ ] `ssh clawnest-homelab` funciona desde compu principal
- [ ] `ssh clawnest-homelab` funciona desde celular con Termux + Tailscale
- [ ] El homelab no se suspende solo
- [ ] El repo está clonado en el homelab
- [ ] **handoff-fase-1.md actualizado**
- [ ] **decisions/002-tailscale-vs-cloudflare.md creado**
- [ ] README actualizado
- [ ] Cambios commiteados y pusheados

---

# FASE 2 — Docker y servicios base
### Duración estimada: 4 horas
### Dónde se trabaja: SSH al Linux Mint desde compu principal
### Agente recomendado: OpenCode con Kimi K2
### Entregable: Qdrant corriendo en Docker, accesible desde la red Tailscale

## Pasos a ejecutar

### Paso 2.1: Instalar Docker en el homelab (via SSH)

Desde la compu principal, conectado por SSH:
- Usar el script oficial: `curl -fsSL https://get.docker.com | sh`
- Agregar el usuario al grupo docker
- Verificar instalación
- Hacer primera prueba con `docker run hello-world`

### Paso 2.2: Docker Compose con Qdrant

Crear `docker-compose.yml` en la raíz del proyecto:
- Imagen oficial: `qdrant/qdrant:latest`
- Puerto 6333 mapeado al host
- Volume persistente para `./data/qdrant`
- Healthcheck configurado
- Restart policy: `unless-stopped`

### Paso 2.3: Levantar Qdrant y validar

- `docker compose up qdrant -d`
- Verificar logs y healthcheck
- Acceder a UI web: `http://clawnest-homelab:6333/dashboard`

### Paso 2.4: Probar Qdrant manualmente

Crear script de exploración para entender insert + search.

### Paso 2.5: Actualizaciones de contexto OBLIGATORIAS

1. Crear `decisions/003-qdrant-vs-pinecone.md`
2. Actualizar `notes/handoff-fase-2.md`
3. Actualizar README
4. Commit + push

## Validaciones antes de pasar a Fase 3

- [ ] Docker instalado y corriendo en el homelab
- [ ] Qdrant corriendo correctamente
- [ ] UI accesible desde compu principal vía Tailscale
- [ ] Comandos Docker básicos comprendidos
- [ ] **handoff-fase-2.md actualizado**
- [ ] **decisions/003-qdrant-vs-pinecone.md creado**
- [ ] Cambios commiteados

---

# FASE 3 — Instalación y configuración de OpenClaw
### Duración estimada: 4 horas
### Dónde se trabaja: SSH al Linux Mint
### Agente recomendado: Claude Code (configuración compleja)
### Entregable: OpenClaw corriendo en el homelab con Kimi K2 como cerebro

## Pasos a ejecutar

### Paso 3.1: Pre-requisitos

- Node.js 20+ instalado en el homelab
- pnpm via corepack

### Paso 3.2: Instalación de OpenClaw

Método "Hackable" (source checkout):

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
corepack enable
pnpm install
```

### Paso 3.3: Onboarding

```bash
pnpm openclaw onboard
```

Configurar:
- Nombre del agente
- Provider de LLM
- Persona base

### Paso 3.4: Configurar OpenRouter como provider

- Provider: OpenAI-compatible
- Base URL: `https://openrouter.ai/api/v1`
- API Key del usuario
- Model: `moonshotai/kimi-k2`

### Paso 3.5: Primera conversación

Probar desde CLI:
- Saludo simple
- Pedirle que recuerde algo
- Nueva sesión: validar memoria persistente

### Paso 3.6: Systemd service

Para arranque automático y restart en caso de fallo.

### Paso 3.7: Actualizaciones de contexto OBLIGATORIAS

1. Crear `decisions/004-kimi-k2-via-openrouter.md`
2. Actualizar `notes/handoff-fase-3.md`
3. Actualizar README
4. Commit + push

## Validaciones antes de pasar a Fase 4

- [ ] OpenClaw responde desde CLI
- [ ] Las respuestas vienen de Kimi K2
- [ ] Memoria persistente funciona
- [ ] systemd service corriendo
- [ ] **handoff-fase-3.md actualizado**
- [ ] **decisions/004-kimi-k2-via-openrouter.md creado**
- [ ] Cambios commiteados

---

# FASE 4 — Integración con Telegram
### Duración estimada: 4 horas
### Dónde se trabaja: SSH al Linux Mint
### Agente recomendado: OpenCode con Kimi K2
### Entregable: agente accesible desde Telegram en el celular

## Pasos a ejecutar

### Paso 4.1: Crear el bot de Telegram

Pasos manuales del usuario:
- Hablar con @BotFather
- `/newbot`, nombre, username
- Guardar token

### Paso 4.2: Configurar Tailscale Funnel

- `sudo tailscale funnel --bg 80`
- Anotar URL pública

### Paso 4.3: Nginx como reverse proxy

Agregar al `docker-compose.yml`:
- Servicio nginx:alpine
- Puerto 80 mapeado
- Volume con `nginx.conf`

Crear `nginx/nginx.conf` con rutas para:
- `/telegram/webhook` → OpenClaw
- `/qdrant/` → dashboard de Qdrant

### Paso 4.4: Integrar Telegram en OpenClaw

- Configurar token del bot
- Configurar URL del webhook
- Auto-registrar con Telegram

### Paso 4.5: Validación end-to-end

Mensajes desde el celular llegan al agente y responde.

### Paso 4.6: Seguridad

Configurar `allowed_users` con tu user ID de Telegram (de @userinfobot).

### Paso 4.7: Actualizaciones de contexto OBLIGATORIAS

1. Crear `decisions/005-telegram-vs-whatsapp.md`
2. Actualizar `notes/handoff-fase-4.md`
3. Actualizar README
4. Commit + push

## Validaciones antes de pasar a Fase 5

- [ ] Bot funciona desde el celular
- [ ] Solo usuarios autorizados pueden hablarle
- [ ] Latencia < 30 segundos
- [ ] **handoff-fase-4.md actualizado**
- [ ] **decisions/005-telegram-vs-whatsapp.md creado**
- [ ] Cambios commiteados

---

# FASE 5 — Memoria extendida con Qdrant
### Duración estimada: 4 horas
### Dónde se trabaja: SSH al Linux Mint + edición de código en compu principal
### Agente recomendado: Claude Code (diseño de arquitectura crítico)
### Entregable: agente con memoria semántica extendida vía Qdrant

## Pasos a ejecutar

### Paso 5.1: Servicio FastAPI para memoria

Crear `skills/memory_service/` con endpoints:
- `POST /memory/remember`
- `POST /memory/recall`
- `GET /memory/health`

Usa `sentence-transformers/all-MiniLM-L6-v2` localmente.

### Paso 5.2: Dockerizar

Dockerfile con:
- Base python:3.11-slim
- Pre-descargar modelo de embedding en build

Agregar al `docker-compose.yml`.

### Paso 5.3: Skill de OpenClaw

Skill `extended_memory` que:
- Detecta intent de "recordá X" → llama `/memory/remember`
- Detecta consultas que requieren memoria → llama `/memory/recall`
- Inyecta resultados en contexto del LLM

### Paso 5.4: Nginx rutea al memory_service

`/memory/` → `http://memory_service:8001/`

### Paso 5.5: Validación

Pruebas semánticas por Telegram.

### Paso 5.6: Actualizaciones de contexto OBLIGATORIAS

1. Crear `decisions/006-memory-architecture.md` (memoria multi-capa)
2. Actualizar `notes/handoff-fase-5.md`
3. Actualizar README
4. Commit + push

## Validaciones antes de pasar a Fase 6

- [ ] memory_service responde en /memory/health
- [ ] El agente guarda y recupera memorias semánticamente
- [ ] **handoff-fase-5.md actualizado**
- [ ] **decisions/006-memory-architecture.md creado**
- [ ] Cambios commiteados

---

# FASE 6 — Job Tracker (skill estrella)
### Duración estimada: 8 horas (día y medio)
### Dónde se trabaja: SSH + compu principal
### Agente recomendado: Mixto — Claude Code para diseño, OpenCode/Kimi para scrapers
### Entregable: skill que busca ofertas y notifica al usuario

## Pasos a ejecutar

### Paso 6.1: Diseño de la skill (Claude Code)

Definir antes de codear:
- Fuentes: Get on Board, RemoteOK, WeWorkRemotely, LinkedIn, Workana
- Keywords: AI Engineer, ML Engineer, LLM Engineer, GenAI Engineer
- Filtros: junior/semi-senior, Python obligatorio, remoto o BA, últimos 7 días

### Paso 6.2: Servicio FastAPI (OpenCode/Kimi)

`skills/job_tracker/` con endpoints:
- `POST /jobs/search`
- `POST /jobs/scheduled`
- `GET /jobs/recent`
- `POST /jobs/save`
- `GET /jobs/saved`

### Paso 6.3: Scrapers/fetchers (OpenCode/Kimi)

Un archivo por fuente, misma interfaz:
- `fetch_recent_jobs() -> list[Job]`

### Paso 6.4: Filtrado con LLM (Claude Code para el prompt)

Kimi K2 evalúa cada job: ¿relevante para AI Engineer Jr con stack Python?

### Paso 6.5: Deduplicación

Hash por URL+título guardado en Qdrant.

### Paso 6.6: Scheduler

Cron o APScheduler para correr cada 6hs.

### Paso 6.7: Integración con OpenClaw

Skill que:
- Recibe ofertas nuevas del scheduler
- Las envía formateadas por Telegram
- Maneja comandos /save, /dismiss, /apply

### Paso 6.8: Validación

24hs de uso real para confirmar que el sistema funciona.

### Paso 6.9: Actualizaciones de contexto OBLIGATORIAS

1. Crear `decisions/007-job-tracker-sources.md`
2. Crear `decisions/008-llm-filtering.md`
3. Actualizar `notes/handoff-fase-6.md`
4. Actualizar README
5. Commit + push

## Validaciones antes de finalizar el MVP

- [ ] Job Tracker corre como servicio independiente
- [ ] Notificaciones llegan automáticamente
- [ ] Filtrado con LLM funciona
- [ ] Deduplicación evita spam
- [ ] Comandos manuales funcionan
- [ ] **handoff-fase-6.md actualizado**
- [ ] **decisions/007 y 008 creados**
- [ ] Cambios commiteados

---

# FASE 7 — Polish, monitoring básico y deploy final
### Duración estimada: 4 horas
### Dónde se trabaja: SSH + compu principal
### Agente recomendado: Claude Code (last mile, calidad importa)
### Entregable: MVP completo, documentado, listo para LinkedIn

## Pasos a ejecutar

### Paso 7.1: Logging estructurado

JSON structured logs en todos los servicios FastAPI con `structlog`.

### Paso 7.2: Manejo de errores

- Kimi K2 caído → fallback a Claude vía OpenRouter
- Qdrant caído → mensaje útil, degradar gracefully
- Telegram rate limit → backoff exponencial
- Fuente de Job Tracker falla → continuar con las demás

### Paso 7.3: Healthchecks completos

Endpoint `/health/full` que verifica todos los servicios.

### Paso 7.4: Backup automático

Daily backup de Qdrant, OpenClaw config, memoria persistente.

### Paso 7.5: README final

README profesional con:
- Descripción
- Demo (gif/video)
- Arquitectura
- Stack
- Cómo replicar
- Roadmap
- Link a ADRs

### Paso 7.6: Repo público

- Verificar que no hay secrets
- Licencia MIT
- Topics relevantes

### Paso 7.7: Post de LinkedIn

Hook: "Tengo un AI Engineer trabajando 24/7 buscándome trabajo mientras yo duermo..."

### Paso 7.8: Handoff note final

`notes/handoff-fase-7-mvp-completo.md` como milestone.

## Validaciones finales

- [ ] Todos los servicios con logs estructurados
- [ ] Sistema degrada gracefully
- [ ] Healthcheck completo funciona
- [ ] Backups configurados
- [ ] README profesional
- [ ] Post de LinkedIn publicado
- [ ] Sistema corre 24/7 sin intervención
- [ ] **handoff final generado**
- [ ] **Todos los ADRs (001-008) completos**

---

# Resumen del MVP

| Fase | Contenido | Duración | Agente recomendado |
|------|-----------|----------|-------------------|
| 0 | Setup de contexto | 1h | Claude Code |
| 1 | Homelab + Tailscale | 4hs | OpenCode/Kimi |
| 2 | Docker + Qdrant | 4hs | OpenCode/Kimi |
| 3 | OpenClaw + Kimi K2 | 4hs | Claude Code |
| 4 | Telegram + Nginx + Funnel | 4hs | OpenCode/Kimi |
| 5 | Memoria extendida | 4hs | Claude Code |
| 6 | Job Tracker | 8hs | Mixto |
| 7 | Polish + deploy | 4hs | Claude Code |
| **Total** | | **33hs (~8 días)** | |

---

# Próximas iteraciones (post-MVP)

**Semana 2:** Application Tracker + LinkedIn Message Crafter
**Semana 3:** Doc Search RAG + Self Observer
**Semana 4:** AI News Digest + Cost Tracker
**Semana 5+:** A definir

---

# Notas finales para IAs implementadoras

**Si sos Claude Code:**
- Lee CLAUDE.md (symlink a AGENTS.md) al inicio
- Usá /compact con prompt custom cuando el contexto pase 60%
- Al terminar tareas: actualizá handoff note + ADRs OBLIGATORIAMENTE

**Si sos OpenCode/Codex/Cursor/otros:**
- Lee AGENTS.md al inicio
- Cuando el contexto se sature, cerrá y abrí sesión nueva
- Antes de cerrar: actualizá handoff note + ADRs OBLIGATORIAMENTE

**Si sos cualquier agente y ves que el handoff note está desactualizado:**
- NO asumas que sabés lo que pasó en sesiones previas
- Preguntale al usuario para llenar los gaps
- Después actualizá el handoff note con la info real

**Comunicación con el usuario (Pablo):**
- Explicar conceptos antes de mostrar código
- Comentarios en español, código en inglés
- Usar analogías
- Pausarse y preguntar si está siguiendo

**Cuándo pausar e involucrar al usuario:**
- Credenciales/API keys
- Decisiones de diseño no especificadas
- Comandos con consecuencias no reversibles
- Antes de borrar datos

---

## Fin del documento técnico

Este documento es la guía para construir el MVP de ClawNest con múltiples
agentes AI. Una vez completado, el sistema corre 24/7 y se itera con nuevas
skills semanalmente.
