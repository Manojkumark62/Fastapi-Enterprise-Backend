# Final Enterprise Challenge

This project implements a tenant-aware Business Management Backend with the following final capabilities:

- Authentication: registration, login, JWT access tokens, refresh rotation, password recovery, session management
- Authorization: ADMIN/MANAGER/USER roles and fine-grained permissions
- Business resources: users, customers, employees, products, orders, payments, tasks, and notifications
- Data lifecycle: CRUD, soft delete/restore, validation, transactions, audit logs, and record history
- Query features: pagination, dynamic filters, keyword search, sorting, bulk create/update/delete
- Documents and data exchange: file upload/download/update/delete, CSV import, filtered CSV export
- Platform integrations: Redis caching and rate limiting, webhooks with replay protection and retries, external API transformation
- Operations: health/readiness checks, background notifications, scheduled cleanup/reminders, async database/API support
- Production: Docker Compose, MySQL, Redis, Alembic migrations, structured logging, workers, and hardened headers

## Final Business API

`GET /api/v1/business/dashboard` returns tenant-scoped operational KPIs:

- customers
- products
- orders
- pending_orders
- revenue
- low_stock_products
- pending_tasks
- unread_notifications

The endpoint is authenticated and uses the same database, tenant, authorization, validation, and response conventions as the rest of the API.

## Verification

Run from the project root after installing dependencies:

```powershell
python -m pytest -q
alembic upgrade head
python -m compileall -q .
```
