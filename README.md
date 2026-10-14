# R1-PMV

Monolito Django para el recorrido interno de una bodega. El corte actual llega a la primera integración: autenticación, producto, carga inicial, apertura de caja y preparación de venta. El cobro, la constancia y el cierre de caja permanecen fuera de este corte.

## Alcance de este corte

| Historia | Estado local | Resultado disponible |
|---|---|---|
| `HU-AUTH-01` | Lista para revisión externa | Login seguro, sesión rotada, navegación y autorización por rol |
| `HU-AUTH-03` | En verificación | Salida confirmada; descarta el borrador activo sin cerrar el turno ni alterar existencias |
| `HU-PROD-02` | Lista para revisión externa | Alta de producto enlatado, validaciones, stock cero y permisos |
| `HU-INV-01a` | En revisión técnica | Carga multilot atómica, costo promedio y pruebas locales; falta carrera PostgreSQL/revisión |
| `HU-CAJA-01` | En progreso | Apertura ligada al vendedor y restricción de turno abierto; falta carrera PostgreSQL/revisión |
| `HU-VEN-01b` | En verificación | Búsqueda por nombre o código, borrador, stock vendible, cantidades y totales sin descuento de existencias |
| `HU-VEN-01c`, `HU-VEN-02a`, `HU-CAJA-02` | Pendiente | Cobro, constancia y cierre aún no están disponibles |

Los estados son evidencia local; este repositorio no modifica por sí mismo Jira ni el remoto de GitHub.

## Requisitos

- Python 3.12 o 3.13.
- Docker Compose y PostgreSQL 17 para las verificaciones de bloqueo y concurrencia.

## Arranque local

1. Copie `.env.example` a `.env`, genere un `DJANGO_SECRET_KEY` local y deje `DATABASE_URL` vacío si usará SQLite.
2. Aplique las migraciones:

   ```powershell
   $env:DJANGO_SECRET_KEY = [guid]::NewGuid().ToString('N')
   .\.venv\Scripts\python.exe manage.py migrate
   ```

3. Defina las tres contraseñas ficticias solo en su sesión y cargue los datos base:

   ```powershell
   $env:SEED_ADMIN_PASSWORD = 'valor-local'
   $env:SEED_WAREHOUSE_PASSWORD = 'valor-local'
   $env:SEED_SELLER_PASSWORD = 'valor-local'
   .\.venv\Scripts\python.exe manage.py seed_pmv
   .\.venv\Scripts\python.exe manage.py runserver
   ```

Las cuentas ficticias son `admin.demo@pmv.invalid`, `almacen.demo@pmv.invalid`, `vendedor.demo@pmv.invalid` e `inactiva.demo@pmv.invalid`. El comando nunca imprime sus contraseñas.

## Rutas del corte

- `/`: ingreso.
- `/inicio/`: panel filtrado por rol.
- `/productos/nuevo/`: registro exclusivo de `ADMIN`.
- `/inventario/carga-inicial/`: carga exclusiva de `ALMACENERO`.
- `/caja/abrir/`: apertura exclusiva de `VENDEDOR`.
- `/ventas/`: preparación exclusiva de `VENDEDOR`; no cobra ni descuenta existencias.

## Verificación

```powershell
$env:DJANGO_SECRET_KEY = 'test-only-key'
$env:APP_ENV = 'test'
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

SQLite cubre los casos funcionales deterministas. Las carreras de dos cargas y dos aperturas deben repetirse con conexiones separadas en PostgreSQL 17 antes de mover `HU-INV-01a` o `HU-CAJA-01` a terminada.

Para PostgreSQL, complete las variables de `.env`, inicie `docker compose up -d db`, ejecute `docker compose --profile tools run --rm migrate` y levante `docker compose up web`. El rol `pmv_migrator` aplica esquema; `pmv_app` conserva privilegios de ejecución limitados.

Consulte [evidencias/CORTE_SEMANA_1_2026-10-13.md](evidencias/CORTE_SEMANA_1_2026-10-13.md) para la trazabilidad del corte y [docs/seguridad.md](docs/seguridad.md) para las decisiones de seguridad.
