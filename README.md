# AW Client Report Portal

Portal de gestión de clientes y generación de reportes PDF para Windbrook Solutions.

## Demo Access

The seeded database includes three pre-configured team accounts. All share the same temporary password and can be changed by each user from the **Account** page after first login. These credentials are intended for demo and review purposes only — they are never exposed anywhere in the UI.

### Recommended reviewer login

Use the **Andrew (admin)** account for a full demo review. It has access to every feature in the portal:

| Username | Password         | Role  |
| -------- | ---------------- | ----- |
| `andrew` | `TempPass2026!`  | admin |

Admin access covers the complete review surface:

- Dashboard (current quarter pill, search, filters, status badges, Recent Reports table)
- Client management (create / edit clients, dynamic retirement, non-retirement and liability accounts, age auto-calc, trust/property address)
- Generate Quarterly Report flow (SACS + TCC) with live calculations and Prepared By attribution
- Per-client report history with re-downloadable SACS and TCC PDFs
- Team Management (`/admin/users`) — create users, reset passwords, assign roles
- Account settings — change own password
- SACS and TCC PDF downloads

### Other available users

| Username  | Password         | Role      |
| --------- | ---------------- | --------- |
| `rebecca` | `TempPass2026!`  | planner   |
| `maryann` | `TempPass2026!`  | assistant |

`planner` and `assistant` have full access to the dashboard, client management, report generation, history and PDF downloads. They **cannot** access Team Management — that area is admin-only and a 403 page is rendered if accessed directly.

### Notes for reviewers

- Credentials live only in this README — there is no "demo credentials" banner inside the portal.
- The seeded demo client (**James & Sarah Patterson**) loads on first run, so the dashboard is never empty.
- To reset back to seeded state at any moment: stop Flask, delete `portal.db`, restart. The three users and the demo client are re-created automatically.
- For production deployment, set the `SECRET_KEY` environment variable and override `DEFAULT_USER_PASSWORD` to change the seed password.

## Setup (2 minutos)

```bash
pip install -r requirements.txt
python app.py
```

Abrir en el browser: http://localhost:5000

## Features implementadas

- ✅ Dashboard de clientes con estado de reportes
- ✅ Alta y edición de clientes (con cuentas dinámicas: retirement, non-retirement, liabilities)
- ✅ Formulario de carga trimestral con valores pre-llenados del perfil
- ✅ Referencia al valor del trimestre anterior (click para usar)
- ✅ Cálculos automáticos en tiempo real:
  - Excess = Inflow - Outflow
  - Private Reserve Target = (6 × Outflow) + Deductibles
  - Totales por sección (retirement C1, C2, non-retirement, grand total)
  - Liabilities separados (NO se restan del net worth)
- ✅ Generación de PDF SACS (cashflow diagram)
- ✅ Generación de PDF TCC (total client chart)
- ✅ Historial de reportes por cliente
- ✅ Cliente demo pre-cargado (James & Sarah Patterson)

## Stack

- Backend: Python + Flask
- Database: SQLite
- PDF: ReportLab
- Frontend: HTML + CSS + JS (vanilla)
