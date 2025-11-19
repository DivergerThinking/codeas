# Documentación de soporte para calificación I+D+i

## 1. Memoria técnica del producto

### Propósito y motivación
- **Producto**: Codeas es un asistente de desarrollo que aprovecha modelos de lenguaje (LLMs) y el contexto completo del repositorio para acelerar tareas de ingeniería de software. Su propuesta central es convertir el conocimiento implícito del código en artefactos concretos (documentos, pruebas, planes de despliegue, refactors) listos para revisión humana.
- **Necesidad**: responde a limitaciones de herramientas existentes mediante mayor control del contexto, previsualización de costes y aplicación selectiva de cambios. Incorpora salvaguardas para proyectos sensibles (control de dominio de contexto, chequeo de costes, vista previa de diffs) que reducen riesgos de sobre-automatización.
- **Audiencia**: equipos de ingeniería que buscan automatizar documentación, pruebas, despliegues y refactorizaciones con trazabilidad y transparencia. También es útil para equipos de compliance y seguridad que requieren auditar cómo se generó cada artefacto.

### Capacidades principales
- Interfaz Streamlit con flujos guiados para generación de documentación, estrategia de despliegue, testing y refactorización, incluyendo formularios específicos por tarea.
- Vistas previas de contexto recuperado (archivos, descripciones y fragmentos) y estimación de costes antes de ejecutar operaciones, lo que habilita control financiero y técnico.
- Selección granular de pasos/fragmentos generados y aplicación automática de cambios en el repositorio, manteniendo historial claro de acciones.
- Gestión de prompts personalizados, chat contextual sobre el código y panel de uso/costes, facilitando iteraciones rápidas y reproducibles.
- Exportación e importación de metadatos para acelerar sesiones posteriores o compartir conocimiento entre equipos.

### Innovación frente al estado del arte
- Combinación de metadatos estructurados y recuperación semántica para limitar el contexto a lo relevante por caso de uso; evita el envío de información redundante y mejora la precisión de las respuestas.
- Automatización supervisada: cada paso es auditable y aplicable selectivamente, reduciendo riesgos de modificaciones masivas. El usuario puede descartar secciones generadas, regenerarlas o aplicarlas parcialmente.
- Multimodelo (OpenAI, Anthropic, Gemini) y multilenguaje de código, con soporte a estrategias y artefactos listos para aplicar (Terraform, test cases, refactors), permitiendo elegir el modelo más adecuado según coste, latencia o políticas internas.
- Integración de métricas de consumo y tokens por flujo, habilitando evaluaciones cuantitativas de eficiencia comparadas con procesos manuales.

## 2. Descripción de arquitectura y metodología

### Pipeline de metadatos
1. **Análisis de archivos**: clasificación por tipo (código, configuración, testing) y extracción de descriptores. Se identifican rutas, componentes y dependencias, permitiendo filtrar posteriormente por dominios técnicos (UI, API, DB, seguridad, infraestructura).
2. **Detalles enriquecidos**: para código se registran responsabilidades, interfaces expuestas, dependencias externas y riesgos potenciales; para tests se describen coberturas previstas, frameworks usados y puntos ciegos. Esto habilita diagnósticos y sugerencias con mayor granularidad.
3. **Persistencia eficiente**: los metadatos se almacenan para su reutilización, evitando reprocesar el repositorio en cada operación. Se prevé versionado de metadatos para comparar cómo evolucionan los componentes y medir impacto de refactors.
4. **Exportación/recarga**: permite generar artefactos de metadatos que pueden compartirse entre ramas o equipos, acelerando auditorías y replicación de escenarios.

### Recuperación de contexto (ContextRetriever)
- Selección de archivos según dominio (p. ej., UI, API, base de datos, seguridad) y profundidad (estructura, resumen o detalle), apoyándose en los descriptores generados por el pipeline.
- Uso de prompts especializados por caso de uso que combinan metadatos, descripciones y secciones de código cuando es necesario; cada prompt define qué tipo de contexto y formato espera, mejorando la consistencia de las respuestas.
- Equilibrio entre precisión y coste: limita tokens enviados al modelo manteniendo información crítica para cada tarea. Incluye estrategias de truncado inteligente y priorización de archivos por relevancia.
- Registro del contexto usado en cada generación, facilitando trazabilidad y reproducibilidad ante auditorías.

### Metodología de interacción
- **Orquestación por agentes**: los agentes deciden qué contexto solicitar y cómo estructurar las salidas (docs, tests, Terraform, refactorizaciones). Cada agente aplica plantillas y validaciones específicas (estructura de secciones, tipos de test esperados, recursos de infraestructura admitidos).
- **Circuito de previsualización**: antes de generar, el usuario revisa contexto y coste estimado; después, valida o descarta secciones generadas. Este ciclo admite regeneraciones incrementales para ajustar la calidad de las salidas.
- **Aplicación controlada**: cambios en archivos se aplican automáticamente respetando la selección del usuario, con posibilidad de revertir. Los diffs o scripts se guardan junto con la información de contexto y prompts utilizados, creando evidencia de cómo se obtuvieron.

## 3. Documentación de casos de uso I+D

### Generación de documentación
- Produce secciones específicas (visión general, arquitectura, APIs, seguridad, UI, base de datos) usando metadatos y contexto seleccionado. Puede incluir diagramas textuales, tablas de endpoints y descripciones de dependencias externas.
- Permite generar y validar cada sección por separado, con trazabilidad al código utilizado. Cada salida referencia los archivos origen y el prompt aplicado, aportando evidencia para auditorías.
- Ejemplo de innovación: transforma el conocimiento implícito del repositorio en documentación curada y reusable, reduciendo el esfuerzo manual típico de extracción y redacción.
- Beneficio adicional: facilita la incorporación de nuevos miembros al equipo y la preparación de entregables de compliance o licitaciones.

### Testing asistido
- El sistema crea estrategias de prueba a partir del análisis de archivos y guías internas (tipos de test, coberturas, dependencias), produciendo planes que cubren rutas felices, bordes y errores.
- Genera casos de prueba concretos listos para implementación, priorizando áreas críticas detectadas en los metadatos (autenticación, manipulación de datos, integraciones externas).
- Beneficio I+D: diseño de QA inteligente que reduce brechas de cobertura y documenta supuestos técnicos. Permite estimar esfuerzo y ordenar la ejecución de pruebas según impacto en riesgo.
- Posibilita la detección de necesidades de mocking o fixtures a partir de dependencias identificadas en el código.

### Estrategia de despliegue y Terraform
- Identifica requisitos de infraestructura del proyecto y propone una estrategia (actualmente focalizada en AWS) alineada con los componentes del código, señalando servicios recomendados, configuraciones de red y políticas de seguridad.
- Genera código Terraform adaptado a la estrategia definida, reutilizando metadatos para configurar servicios y dependencias. Incluye módulos reutilizables y variables parametrizadas para facilitar entornos múltiples.
- Impacto: acelera la creación de entornos reproducibles y seguros a partir de la estructura real del software, reduciendo errores de configuración inicial y mejorando la coherencia entre entornos.
- Puede sugerir estrategias de migración o despliegue progresivo (blue/green, canary) cuando detecta servicios críticos.

### Refactorización guiada
- Clasifica grupos de archivos candidatos a mejora, propone estrategias de refactor y genera diffs o instrucciones aplicables, priorizando deuda técnica visible en los metadatos (duplicidad, acoplamiento, falta de tests).
- Usa recuperación contextual para limitar cambios al ámbito relevante y documenta el razonamiento detrás de cada propuesta, incluyendo riesgos y pasos de validación posteriores.
- Resultado: mantenimiento preventivo asistido que reduce deuda técnica con menor riesgo y con evidencia clara de motivación y alcance.
- Se pueden encadenar refactors con generación de tests para validar el impacto de los cambios.

## 4. Evidencias de novedad y madurez

### Hitos y evolución tecnológica
- **UI y experiencia**: primera versión en Streamlit con flujos guiados y vistas previas; evolución hacia paneles de coste y control de contexto. Próximos hitos incluyen personalización de layouts y soporte a plantillas de entregables.
- **Agentes y prompts especializados**: incorporación de agentes por dominio (documentación, testing, despliegue, refactor) con prompts diferenciados y selección dinámica de metadatos. Iteraciones recientes añadieron prompts de recuperación para detectar gaps de seguridad y observabilidad.
- **Recuperación optimizada**: mejoras en clasificación y descripciones de archivos que reducen coste de tokens y aumentan precisión contextual. Se incorporan heurísticas para priorizar archivos con mayor centralidad en el grafo de dependencias.
- **Multimodelo y multilenguaje**: soporte progresivo a OpenAI, Anthropic y Gemini, ampliando la cobertura de lenguajes y stacks de infraestructura. Se documentan comparativas de coste/latencia y criterios de selección por tipo de tarea.
- **Ecosistema de metadatos**: exportación/importación, versionado y validación de consistencia para asegurar que las sesiones usen información actualizada y verificable.

### Resultados cuantificables
- Reducción de coste/tiempo al reutilizar metadatos y limitar el contexto enviado al LLM. En pruebas internas, la preparación de documentación se reduce de horas a minutos con trazabilidad automática.
- Mayor trazabilidad: cada sección generada mantiene referencia al contexto utilizado, facilitando auditorías y revisiones cruzadas entre equipos.
- Incremento de cobertura de QA y seguridad mediante estrategias de prueba y análisis de dependencias automatizados; permite detectar rutas sin tests y dependencias críticas sin validación.
- Disminución de errores de infraestructura gracias a plantillas Terraform consistentes y alineadas con el código fuente.

## 5. Justificación de impacto y beneficios

### Eficiencia operativa
- **Automatización supervisada**: disminuye el tiempo de documentación, diseño de pruebas y despliegue manteniendo control humano en cada paso. Las vistas previas permiten iteraciones rápidas sin comprometer la calidad.
- **Selección contextual**: evita enviar información irrelevante, reduciendo costes de cómputo y riesgos de filtrado de datos. Al enfocarse en archivos clave, también reduce el tiempo de revisión de los expertos.
- **Reutilización de artefactos**: los metadatos y prompts pueden versionarse y compartirse, permitiendo replicar procesos con mínima fricción.

### Calidad y seguridad
- **Trazabilidad completa**: las salidas (docs, tests, Terraform, diffs) se vinculan al contexto de origen, facilitando revisiones y cumplimiento. Cada artefacto conserva referencias a archivos y prompts empleados.
- **Prevención de errores**: previsualización y aplicación selectiva minimizan el riesgo de cambios incorrectos en código crítico. Se pueden registrar puntos de control o checklists asociados a cada acción.
- **Protección de información sensible**: la selección de contexto evita exponer archivos no requeridos, lo que ayuda a cumplir políticas de mínimo privilegio en entornos regulados.

### Innovación aplicada
- **Metadatos estructurados**: clasificación y descripciones enriquecidas permiten adaptar prompts a dominios específicos (UI, API, DB, seguridad, QA). Esto habilita flujos verticalizados que producirían mejores resultados que prompts genéricos.
- **Artefactos listos para uso**: genera scripts de infraestructura, casos de prueba y diffs aplicables, acelerando la entrega de valor. El usuario puede ejecutar o aplicar estos artefactos directamente tras revisión.
- **Ciclo cerrado de mejora**: combina generación, validación y aplicación en un mismo flujo, capturando retroalimentación para ajustar prompts y metadatos en siguientes iteraciones.

## 6. Pruebas de concepto y casos demostrativos

### Ejemplos sugeridos
1. **Generación de documentación**: captura de entrada (selección de contexto) y salida de secciones de arquitectura, APIs y seguridad. Añadir comparación entre versión generada automáticamente y una versión manual previa, señalando ahorros de tiempo.
2. **Estrategia de testing**: guías de tipos de prueba, detección de áreas críticas y casos concretos propuestos. Complementar con la implementación de uno o dos casos y su resultado de ejecución.
3. **Plan de despliegue y Terraform**: estrategia para AWS con recursos derivados del código y scripts Terraform generados. Incluir validación con `terraform plan` y evidencias de conformidad con políticas internas.
4. **Refactorización**: lista de archivos candidatos, plan de cambios y diff aplicado en un módulo específico. Acompañar con ejecución de tests relacionados para demostrar no regresión.
5. **Chat contextual**: conversación guiada para resolver dudas de arquitectura o seguridad usando el contexto recuperado, mostrando precisión y rapidez frente a búsquedas manuales.

### Trazabilidad y anexos
- Para cada caso, incluir: contexto seleccionado (archivos y descripciones), prompt utilizado, salida generada y resultado aplicado (si procede). Adjuntar hashes o referencias de commit para asegurar reproducibilidad.
- Incorporar capturas o logs de la interfaz Streamlit mostrando la previsualización de contexto, el control de costes y las decisiones de aplicación de cambios.
- Documentar las métricas obtenidas (tokens usados, tiempo de procesamiento, cobertura de prueba generada) como evidencia objetiva de eficiencia. Añadir análisis comparativo entre modelos usados y su impacto en coste/calidad.
- Mantener un repositorio de artefactos (documentos generados, scripts Terraform, planes de test, diffs) etiquetado por fecha y caso de uso para facilitar auditorías y evolución.
