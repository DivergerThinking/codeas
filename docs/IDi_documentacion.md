# Documentación de soporte para calificación I+D+i

## 1. Memoria técnica del producto

### Propósito y motivación
- **Producto**: Codeas es un asistente de desarrollo que aprovecha modelos de lenguaje (LLMs) y el contexto completo del repositorio para acelerar tareas de ingeniería de software.
- **Necesidad**: responde a limitaciones de herramientas existentes mediante mayor control del contexto, previsualización de costes y aplicación selectiva de cambios.
- **Audiencia**: equipos de ingeniería que buscan automatizar documentación, pruebas, despliegues y refactorizaciones con trazabilidad y transparencia.

### Capacidades principales
- Interfaz Streamlit con flujos guiados para generación de documentación, estrategia de despliegue, testing y refactorización.
- Vistas previas de contexto recuperado y estimación de costes antes de ejecutar operaciones.
- Selección granular de pasos/fragmentos generados y aplicación automática de cambios en el repositorio.
- Gestión de prompts personalizados, chat contextual sobre el código y panel de uso/costes.

### Innovación frente al estado del arte
- Combinación de metadatos estructurados y recuperación semántica para limitar el contexto a lo relevante por caso de uso.
- Automatización supervisada: cada paso es auditable y aplicable selectivamente, reduciendo riesgos de modificaciones masivas.
- Multimodelo (OpenAI, Anthropic, Gemini) y multilenguaje de código, con soporte a estrategias y artefactos listos para aplicar (Terraform, test cases, refactors).

## 2. Descripción de arquitectura y metodología

### Pipeline de metadatos
1. **Análisis de archivos**: clasificación por tipo (código, configuración, testing) y extracción de descriptores.
2. **Detalles enriquecidos**: para código se registran responsabilidades y elementos clave; para tests se describen coberturas previstas.
3. **Persistencia eficiente**: los metadatos se almacenan para su reutilización, evitando reprocesar el repositorio en cada operación.

### Recuperación de contexto (ContextRetriever)
- Selección de archivos según dominio (p. ej., UI, API, base de datos, seguridad) y profundidad (estructura, resumen o detalle).
- Uso de prompts especializados por caso de uso que combinan metadatos, descripciones y secciones de código cuando es necesario.
- Equilibrio entre precisión y coste: limita tokens enviados al modelo manteniendo información crítica para cada tarea.

### Metodología de interacción
- **Orquestación por agentes**: los agentes deciden qué contexto solicitar y cómo estructurar las salidas (docs, tests, Terraform, refactorizaciones).
- **Circuito de previsualización**: antes de generar, el usuario revisa contexto y coste estimado; después, valida o descarta secciones generadas.
- **Aplicación controlada**: cambios en archivos se aplican automáticamente respetando la selección del usuario, con posibilidad de revertir.

## 3. Documentación de casos de uso I+D

### Generación de documentación
- Produce secciones específicas (visión general, arquitectura, APIs, seguridad, UI, base de datos) usando metadatos y contexto seleccionado.
- Permite generar y validar cada sección por separado, con trazabilidad al código utilizado.
- Ejemplo de innovación: transforma el conocimiento implícito del repositorio en documentación curada y reusable.

### Testing asistido
- El sistema crea estrategias de prueba a partir del análisis de archivos y guías internas (tipos de test, coberturas, dependencias).
- Genera casos de prueba concretos listos para implementación, priorizando áreas críticas detectadas en los metadatos.
- Beneficio I+D: diseño de QA inteligente que reduce brechas de cobertura y documenta supuestos técnicos.

### Estrategia de despliegue y Terraform
- Identifica requisitos de infraestructura del proyecto y propone una estrategia (actualmente focalizada en AWS) alineada con los componentes del código.
- Genera código Terraform adaptado a la estrategia definida, reutilizando metadatos para configurar servicios y dependencias.
- Impacto: acelera la creación de entornos reproducibles y seguros a partir de la estructura real del software.

### Refactorización guiada
- Clasifica grupos de archivos candidatos a mejora, propone estrategias de refactor y genera diffs o instrucciones aplicables.
- Usa recuperación contextual para limitar cambios al ámbito relevante y documenta el razonamiento detrás de cada propuesta.
- Resultado: mantenimiento preventivo asistido que reduce deuda técnica con menor riesgo.
