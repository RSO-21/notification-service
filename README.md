# Notification Service

The **Notification Service** is responsible for creating and serving user notifications based on system events.  
It is implemented as an **event-driven microservice** and integrates with the rest of the system via **RabbitMQ**.

---

## Responsibilities

- Consume `payment_confirmed` events from RabbitMQ
- Store notifications in PostgreSQL
- Expose an HTTP API for frontend notification retrieval
- Support multi-tenant database schemas via `X-Tenant-ID`

---

## Architecture

**Event flow:**
Payment Service -> payment_confirmed (RabbitMQ event) -> RabbitMQ -> Notification Consumer -> PostgreSQL -> Notification HTTP API → Frontend

Notifications are handled **asynchronously**, which avoids tight coupling between services and allows independent scaling.

---

## Communication

### Inbound
- **RabbitMQ**
  - Queue: `payment_confirmed`
  - Event-driven (asynchronous)

### Outbound
- **HTTP (REST)**
  - Used by frontend to fetch notifications

No direct synchronous (gRPC) communication is used for notifications, as notifications are asynchronous by nature.

---

## API Endpoints

### Get notifications
```http
GET /notifications?user_id={userId}&unread_only={true|false}
Headers:
  X-Tenant-ID: public
``` 

### Mark notifications as read
```http
POST /notifications/{notification_id}/read
Headers:
  X-Tenant-ID: public
```
