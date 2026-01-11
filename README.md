# Notification Service

Notification Service is a FastAPI microservice responsible for storing and exposing user notifications in a multi-tenant microservices system.
Notifications are created asynchronously based on events from other services ( payment status updates) and can be queried and marked as read by users.

## Responsibilities

* Storing user notifications
* Receiving and processing events from RabbitMQ
* Exposing notification data via REST API
* Marking notifications as read
* Tenant isolation using PostgreSQL schemas
* Health and readiness checks
* Prometheus metrics exposure

## Tech Stack

* **FastAPI**
* **SQLAlchemy**
* **PostgreSQL** (schema-per-tenant)
* **RabbitMQ** (event consumption)
* **Docker**
* **GitHub Actions**
* **pytest**
* **Prometheus FastAPI Instrumentator**

## Multi-Tenancy

* Tenant is selected by request header:

  ```
  X-Tenant-Id: <tenant_name>
  ```

* If the tenant header is not provided, it defaults to `public`

* Each tenant is isolated using a dedicated PostgreSQL schema

## Architecture Overview

* **REST API** – used by frontend or API Gateway to list and update notifications
* **RabbitMQ Consumer** – listens for payment-related events and creates notifications
* **PostgreSQL** – stores notifications in tenant-specific schemas

The RabbitMQ consumer runs as a **separate container/deployment** from the API service.

## API Endpoints

### Notifications

* `GET /notifications`

Lists notifications for a given user.

**Query parameters:**

* `user_id` (required)
* `unread_only` (optional, default `false`)
* `limit` (optional, default `50`)

Notifications are returned ordered by creation time (newest first).

* `POST /notifications/{notification_id}/read`

Marks a notification as read.

Returns **404** if the notification does not exist.


### Health

* `GET /health`

Health/readiness endpoint.

* Verifies database connectivity by executing a simple query
* Returns **200** if the database is reachable
* Returns **503** if the database is unavailable

## Event Consumption (RabbitMQ)

The service listens to a payment confirmation queue and creates notifications based on incoming messages.

**Expected message fields (JSON):**

```json
{
  "tenant_id": "tenant1",
  "user_id": "123",
  "order_id": "456",
  "payment_id": "789",
  "payment_status": "PAID",
  "amount": 99.99
}
```

**Behavior:**

* Creates a notification per event
* Uses tenant-specific schema based on `tenant_id`
* Acknowledges messages even on failure to avoid retry loops

## Testing

Tests cover:

* Notification listing and ordering
* Marking notifications as read
* Tenant isolation between schemas
* Health endpoint behavior
* Database failure handling via dependency overrides

Run tests locally:

```powershell
python -m pytest
```

## CI/CD

On push to `main`:

1. Run tests
2. Build Docker image
3. Push image to Azure Container Registry

The Docker image is not built or pushed if tests fail.