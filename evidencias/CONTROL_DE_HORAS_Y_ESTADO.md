# Control de horas y estado — Sprint 1

**Propósito:** mantener trazabilidad profesional entre la estimación aprobada en Jira, el trabajo realmente realizado y la evidencia disponible. Este archivo no reemplaza el *worklog* de Jira.

## Regla de registro

1. La columna **Estimación Jira** es planificación; nunca se presenta como horas consumidas.
2. La columna **Tiempo real registrado** se completa al finalizar una sesión real, con inicio, fin y actividad verificable.
3. Un ítem se mueve a `En revisión` solamente cuando su evidencia cubre el alcance comprometido; se mueve a `Hecho` tras revisión independiente.
4. Si existe una dependencia no implementada, el estado es `Bloqueado` o `En progreso`; no se rellena una ficha de cierre.

## Estado al 2026-10-11

| Ítem | Jira | Estimación Jira | Trabajo real verificado | Estado recomendado | Tiempo real registrado |
|---|---|---:|---|---|---|
| S1-SEC-01 | SCRUM-297 | 4 h | Configuración por entorno, archivos de secretos y diseño de roles PostgreSQL | En progreso | Sin registro horario: no declarar horas en Jira aún |
| S1-SEC-02 | SCRUM-298 | 4 h | Baseline de sesión, CSRF, cookies, cabeceras, redacción y autorización base | En progreso | Sin registro horario: no declarar horas en Jira aún |
| S1-DB-04 | SCRUM-295 | 3 h | Comando de semillas idempotentes y prueba local ejecutada dos veces | En revisión | Sin registro horario: no declarar horas en Jira aún |
| S1-AUTH01-SVC | SCRUM-306 | 4 h | Servicio de autenticación, sesión y casos positivos/negativos automatizados | En revisión | Sin registro horario: no declarar horas en Jira aún |
| S1-AUTH01-AUTHZ | SCRUM-307 | 3 h | Matriz de roles y rutas protegidas de integración | En progreso | Sin registro horario: no declarar horas en Jira aún |
| S1-AUTH01-AUTO | SCRUM-308 | 3 h | Suite local para CA 1–4 sobre contratos actuales | En revisión | Sin registro horario: no declarar horas en Jira aún |
| S1-AUTH03-SVC | SCRUM-312 | 3 h | Solo invalidación básica de sesión | Bloqueado | Sin registro horario: no declarar horas en Jira aún |

**Total de estimaciones de los ítems con avance:** 24 h. Esto no significa que se hayan consumido 24 h.

## Corte local al 2026-10-13

La implementación avanzó después del registro histórico anterior. Este cuadro no inventa horas ni modifica Jira; resume únicamente el estado verificable del workspace.

| Grupo | Jira | Resultado local verificable | Estado recomendado sin revisión externa | Tiempo real registrado |
|---|---|---|---|---|
| HU-AUTH-01 | SCRUM-305..310 | UI, servicio, sesión rotada, autorización y pruebas CA1–4 | En revisión | No registrado; no declarar horas retrospectivas |
| HU-PROD-02 | SCRUM-316..320 | UI, servicio, constraints, stock cero y pruebas CA1–5 | En revisión | No registrado; no declarar horas retrospectivas |
| HU-INV-01a | SCRUM-321..326 | UI, validación, transacción multilot y pruebas locales; concurrencia PostgreSQL pendiente | En progreso / revisión técnica | No registrado; no declarar horas retrospectivas |
| HU-CAJA-01 | SCRUM-327..332 | UI, servicio e índice único parcial; carrera PostgreSQL pendiente | En progreso | No registrado; no declarar horas retrospectivas |
| AUTH-03, VEN-01b, VEN-01c, VEN-02a, CAJA-02 | SCRUM-311..315, 333..355 | Sin recorrido funcional del alcance de semana 2 | Por hacer | 0 h declaradas desde este corte |

Detalle y comandos: [CORTE_SEMANA_1_2026-10-13.md](CORTE_SEMANA_1_2026-10-13.md).

## Bitácora de sesiones reales

Duplica esta plantilla por cada sesión y registra la misma entrada en Jira. No agregues sesiones retrospectivas sin una fuente verificable.

```text
Fecha (America/Lima):
Inicio:
Fin:
Duración calculada:
Ítem Jira:
Actividad realizada:
Archivos / URL de PR / commit:
Prueba o revisión ejecutada:
Resultado:
Dependencia o bloqueo:
Responsable que registra:
```

## Próxima evidencia necesaria

| Ítem | Para mover de estado con fundamento |
|---|---|
| SCRUM-297 | Instalar Docker/PostgreSQL 17, levantar Compose y conservar evidencia de los roles con privilegios mínimos. |
| SCRUM-298 | Revalidar CSRF/autorización en PostgreSQL y completar los servicios reales de ventas de la segunda semana. |
| SCRUM-295 | Ejecutar las semillas dos veces contra PostgreSQL 17 y adjuntar conteos reproducibles. |
| SCRUM-305..310 | Ejecutar QA manual de login, obtener revisión independiente y adjuntar PR/CI antes de marcar AUTH-01 Hecho. |
| SCRUM-316..320 | Ejecutar QA manual de producto, obtener revisión independiente y adjuntar PR/CI antes de marcar PROD-02 Hecho. |
| SCRUM-321..326 | Ejecutar la carrera de carga en PostgreSQL, QA manual y revisión independiente. |
| SCRUM-327..332 | Ejecutar dos aperturas sincronizadas en PostgreSQL, QA manual y revisión independiente. |
| SCRUM-312 | Implementar borrador/turno y demostrar descarte atómico, propiedad del turno y reingreso. |
