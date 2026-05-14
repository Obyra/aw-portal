# AW Client Report Portal

Portal de gestión de clientes y generación de reportes PDF para Windbrook Solutions.

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
