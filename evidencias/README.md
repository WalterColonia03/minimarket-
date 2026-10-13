# Índice de evidencias — Sprint 1

**Última ejecución local:** 2026-10-13 (`America/Lima`)

**Entorno:** Python 3.12.10, Django 5.2.18, SQLite de pruebas.

**Alcance:** evidencia técnica local; no cambia responsables, worklogs ni estados de Jira.

El estado consolidado de este corte está en [CORTE_SEMANA_1_2026-10-13.md](CORTE_SEMANA_1_2026-10-13.md). El control entre estimación y tiempo real está en [CONTROL_DE_HORAS_Y_ESTADO.md](CONTROL_DE_HORAS_Y_ESTADO.md).

## Resultado común reproducible

```powershell
$env:DJANGO_SECRET_KEY = 'valor-efimero-solo-pruebas'
$env:APP_ENV = 'test'
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test --verbosity 1
```

```text
No changes detected
System check identified no issues (0 silenced).
45 tests ejecutados
OK
```

## Evidencias anteriores conservadas

| Subtarea | Jira | Ficha |
|---|---|---|
| S1-SEC-01 | SCRUM-297 | [resultado](TRANSVERSAL/S1-SEC-01/resultado-prueba.md) |
| S1-SEC-02 | SCRUM-298 | [resultado](TRANSVERSAL/S1-SEC-02/resultado-prueba.md) |
| S1-DB-04 | SCRUM-295 | [resultado](TRANSVERSAL/S1-DB-04/resultado-prueba.md) |
| S1-DB-05 | SCRUM-296 | [resultado](TRANSVERSAL/S1-DB-05/resultado-prueba.md) |
| S1-AUTH01-SVC | SCRUM-306 | [resultado](HU-AUTH-01/S1-AUTH01-SVC/resultado-prueba.md) |
| S1-AUTH01-AUTHZ | SCRUM-307 | [resultado](HU-AUTH-01/S1-AUTH01-AUTHZ/resultado-prueba.md) |
| S1-AUTH01-AUTO | SCRUM-308 | [resultado](HU-AUTH-01/S1-AUTH01-AUTO/resultado-prueba.md) |
| S1-AUTH03-SVC | SCRUM-312 | [resultado parcial](HU-AUTH-03/S1-AUTH03-SVC/resultado-prueba.md) |

Las cinco historias destinadas a la segunda semana permanecen pendientes. No se genera evidencia de terminación para funcionalidad que no existe.
