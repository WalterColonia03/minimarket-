# Corte técnico de la primera semana — 2026-10-13

## Alcance aplicado

Este corte sigue `20_Corte_De_Exposicion_Martes.md` y la solicitud del propietario del workspace. Se trabajó únicamente sobre la copia local `r1-pmv/`; no se ejecutaron `git push`, creación de PR, cambios en GitHub ni transiciones/worklogs en Jira.

Las horas de Jira son estimaciones. No se convierten en tiempo real ni se registran retrospectivamente desde este documento.

## Contraste de solo lectura con Jira

El 2026-10-13 se consultó Jira mediante el conector de solo lectura. El Sprint `Sprint 1 — PMV` figura activo, con inicio `2026-10-10 21:11` y fin `2026-10-23 23:59` en `America/Lima`.

| Grupo | Estado observado en Jira antes de esta entrega local |
|---|---|
| `HU-AUTH-01` / SCRUM-305..310 | Story y seis subtareas `Finalizada` |
| `HU-PROD-02` / SCRUM-316..320 | Story y cinco subtareas `Tareas por hacer` |
| `HU-INV-01a` / SCRUM-321..326 | Story y seis subtareas `Tareas por hacer` |
| `HU-CAJA-01` / SCRUM-327..332 | Story `Tareas por hacer`; UI `Finalizada`; SVC/CONC `En curso`; AUTO `En revisión`; MAN/REV `Tareas por hacer` |
| `HU-AUTH-03` / SCRUM-311..315 | Story `En curso`; UI `Finalizada`; REV `En curso`; las otras tres subtareas `Tareas por hacer` |
| Venta, constancia y cierre / SCRUM-333..355 | Todas las subtareas `Tareas por hacer` |

Esta consulta detecta que el código local y el tablero no están sincronizados. Por instrucción del propietario, no se corrigió ningún estado, descripción, responsable, evidencia ni worklog en Jira.

| Historia | Jira / subtareas | Estado técnico local | Evidencia actual | Pendiente para cierre formal |
|---|---|---|---|---|
| `HU-AUTH-01` | `SCRUM-215` / `SCRUM-305..310` | Funcional, lista para revisión externa | Login accesible, mensaje uniforme, sesión rotada, menú por rol, POST/URL prohibidos y pruebas Django | Caso manual con capturas, revisión independiente, PR/CI y transición Jira |
| `HU-PROD-02` | `SCRUM-233` / `SCRUM-316..320` | Funcional, lista para revisión externa | Modelo/constraints, servicio, formulario, categoría activa, precio/minimo, código normalizado único, stock cero y pruebas | Caso manual con navegador, revisión independiente, PR/CI y transición Jira |
| `HU-INV-01a` | `SCRUM-242` / `SCRUM-321..326` | En revisión técnica; Story aún En progreso | UI multilot, validación Lima, transacción atómica, unicidad, costo promedio `HALF_UP`, FEFO y pruebas SQLite | `CT-CONC-01` con dos conexiones PostgreSQL, caso manual, revisión independiente |
| `HU-CAJA-01` | `SCRUM-255` / `SCRUM-327..332` | En progreso | UI, servicio, vendedor desde sesión, monto decimal, bloqueo transaccional e índice único parcial de turno `OPEN` | `CT-CONC-02` real en PostgreSQL, caso manual y revisión independiente |
| `HU-AUTH-03` | `SCRUM-217` / `SCRUM-311..315` | Pendiente · semana 2 | Solo existe salida básica de seguridad; no hay borrador integrado | Implementación completa y sus pruebas |
| `HU-VEN-01b` | `SCRUM-263` / `SCRUM-333..337` | Pendiente · semana 2 | Ninguna funcionalidad de venta; la ruta muestra el límite de alcance | Implementación completa |
| `HU-VEN-01c` | `SCRUM-264` / `SCRUM-338..345` | Pendiente · semana 2 | No implementada | Implementación completa |
| `HU-VEN-02a` | `SCRUM-265` / `SCRUM-346..350` | Pendiente · semana 2 | No implementada | Implementación completa |
| `HU-CAJA-02` | `SCRUM-256` / `SCRUM-351..355` | Pendiente · semana 2 | No implementada | Implementación completa |

## Verificación reproducible

Ambiente: Windows, Python 3.12.10, Django 5.2.18, `APP_ENV=test`, SQLite aislado del runner.

```powershell
$env:DJANGO_SECRET_KEY = 'valor-efimero-solo-pruebas'
$env:APP_ENV = 'test'
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test --verbosity 1
```

Resultado del último control del corte:

```text
No changes detected
System check identified no issues (0 silenced).
45 tests ejecutados
OK
```

Los `403 Forbidden` y un `404 Not Found` emitidos durante la suite son casos negativos esperados: comprueban autorización por rol y propiedad del turno sin mutación.

## Límites de evidencia

- El cliente Docker está instalado, pero el daemon no estaba activo; no se ejecutaron PostgreSQL 17 ni las carreras `CT-CONC-01`/`CT-CONC-02`.
- No hay evidencia de CI remoto, PR o revisión humana independiente porque el propietario pidió no modificar GitHub/Jira.
- Las vistas se renderizaron mediante el cliente de pruebas Django. No se fabricaron capturas de navegador ni se declaró QA manual no ejecutado.
- Por esos límites, “funcional” no equivale a “Hecho en Jira”. El propietario decide las transiciones después de adjuntar la revisión requerida.
