# CLAUDE.md - Instrucciones para Claude

## Descripción del Proyecto

**Codeas** (CODEbase ASsistant) es una herramienta de desarrollo asistida por IA que utiliza LLMs para mejorar procesos de desarrollo mediante análisis de contexto completo del código. Desarrollado por **Diverger Thinking**.

- **Versión**: 0.4.1
- **Lenguaje**: Python 3.9-3.11
- **Framework UI**: Streamlit
- **Licencia**: MIT

## Estructura del Proyecto

```
src/codeas/
├── main.py                 # Punto de entrada (inicia Streamlit UI)
├── configs/                # Configuración y prompts
│   ├── agents_configs.py   # Configuraciones de agentes
│   ├── llm_params.py       # Parámetros de modelos LLM
│   └── prompts.py          # Templates de prompts
├── core/                   # Lógica de negocio principal
│   ├── agent.py            # Orquestación de agentes
│   ├── clients.py          # Clientes multi-modelo LLM
│   ├── llm.py              # Wrapper de cliente LLM
│   ├── metadata.py         # Generación de metadatos
│   ├── repo.py             # Indexación de repositorios
│   ├── retriever.py        # Recuperación de contexto
│   ├── state.py            # Gestión de estado de sesión
│   └── usage_tracker.py    # Tracking de costos
├── use_cases/              # Implementaciones de casos de uso
│   ├── documentation.py    # Generación de documentación
│   ├── deployment.py       # Planificación de despliegue
│   ├── testing.py          # Estrategias de testing
│   └── refactoring.py      # Recomendaciones de refactoring
└── ui/                     # Interfaz Streamlit
    ├── 🏠_Home.py          # Página principal
    ├── pages/              # Páginas de funcionalidades
    └── components/         # Componentes reutilizables
```

## Comandos Útiles

```bash
# Instalar dependencias
pip install -e .

# Ejecutar la aplicación
codeas

# Formateo de código
make style

# Ejecutar con Streamlit directamente
streamlit run src/codeas/ui/🏠_Home.py
```

## Stack Tecnológico

| Componente | Tecnología |
|------------|------------|
| Lenguaje | Python 3.9-3.11 |
| UI | Streamlit 1.28+ |
| Validación | Pydantic 2.5+ |
| LLM Providers | OpenAI, Anthropic, Google Gemini |
| Token Counting | tokencost |
| Code Quality | black, isort, ruff |

## Convenciones de Código

- **Formateo**: Usar `make style` (black + isort + ruff)
- **Validación de datos**: Pydantic BaseModel para todas las estructuras de datos
- **Tipado**: Type hints obligatorios en funciones públicas
- **Documentación**: Docstrings en español para funciones principales
- **Imports**: Ordenados con isort (perfil black)

## Arquitectura Clave

### Módulos Core

1. **State** (`core/state.py`): Gestión centralizada del estado de sesión
2. **Repo** (`core/repo.py`): Indexación y filtrado de archivos del repositorio
3. **Metadata** (`core/metadata.py`): Clasificación y extracción de metadatos de archivos
4. **Retriever** (`core/retriever.py`): Selección de contexto relevante para LLM
5. **Agent** (`core/agent.py`): Normalización de interacciones con LLM

### Patrones de Diseño

- **Metadata-Driven**: Metadatos pre-computados reducen costos de tokens
- **Supervised Automation**: Flujo Preview → Review → Apply
- **Multi-Model Support**: Capa de abstracción para múltiples proveedores LLM
- **Cost Transparency**: Tracking completo de tokens/costos

### Flujo de Trabajo

1. Usuario selecciona repositorio en Home
2. Generación de metadatos (o carga de caché)
3. Aplicación de filtros por página
4. Fase de preview con estimación de costos
5. Generación ejecuta LLM con contexto seleccionado
6. Review y selección de outputs
7. Aplicación escribe artefactos al filesystem
8. Tracking registra uso y costos

## Datos de Runtime

Todos los datos de ejecución se almacenan en `.codeas/`:
- `metadata.json`: Metadatos cacheados
- `filters.json`: Patrones de filtrado por página
- `outputs/`: Artefactos generados
- `usage.json`: Tracking de costos

## Casos de Uso Principales

1. **Documentation**: Genera 8 secciones de documentación automática
2. **Deployment**: Análisis de infraestructura y generación de Terraform
3. **Testing**: Estrategias de test y casos de prueba
4. **Refactoring**: Identificación de mejoras y generación de diffs

## Variables de Entorno

```bash
OPENAI_API_KEY=sk-...        # API key de OpenAI
ANTHROPIC_API_KEY=sk-ant-... # API key de Anthropic
GOOGLE_API_KEY=...           # API key de Google Gemini
```

## Consideraciones para Desarrollo

- El proyecto usa emojis en nombres de archivos UI (ej: `🏠_Home.py`)
- Los prompts están centralizados en `configs/prompts.py` (~28KB)
- La documentación principal está en español
- Persistencia de estado mediante archivos JSON en `.codeas/`
- No modificar directamente `metadata.json` - se regenera automáticamente
