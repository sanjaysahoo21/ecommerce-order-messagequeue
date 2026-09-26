# Event-Driven E-Commerce Order Fulfillment System

This project is a multi-service e-commerce order fulfillment system built using an event-driven architecture with Spring Boot and RabbitMQ.

## Architecture

The system consists of 5 microservices communicating asynchronously via RabbitMQ:
1. **Order Service (Port 8080)**: Entry point. Accepts orders and publishes `OrderCreated`.
2. **Payment Service**: Listens for `OrderCreated`, processes payment, and publishes `PaymentProcessed`.
3. **Inventory Service**: Listens for `PaymentProcessed`, reserves inventory, and publishes `InventoryReserved`.
4. **Shipping Service**: Listens for `InventoryReserved`, creates a shipment, and publishes `ShipmentCreated`.
5. **Notification Service**: Listens to all events and logs notifications.

Each service (except Notification) uses its own isolated logical PostgreSQL database to ensure data autonomy.

## Prerequisites
- Docker and Docker Compose
- Java 21 (if running locally without Docker)
- Maven (if running locally without Docker)

## Setup and Running

1. Clone the repository and navigate to the project root.
2. Copy `.env.example` to `.env` if you want to override defaults.
3. Start the entire system using Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
4. Wait a couple of minutes for all containers to be healthy. The databases and RabbitMQ will start first, followed by the Spring Boot microservices.

## API Endpoints

### Create an Order
```bash
curl -X POST http://localhost:8080/api/orders \
-H "Content-Type: application/json" \
-d '{
  "items": [
    {"productId": "prod-123", "quantity": 2, "price": 10.50}
  ],
  "totalPrice": 21.00
}'
```
You will receive a `202 Accepted` response with the new `orderId`.

### Check Order Status
```bash
curl http://localhost:8080/api/orders/{orderId}
```
You will receive a `200 OK` response. Wait a few seconds after creating the order, and the status should transition to `SHIPPED`.

### Testing Dead Letter Queue (DLQ)
The Inventory Service is designed to fail if it encounters an order with the `productId: "FAIL-ME"`.
To test this, create an order with this product ID:
```bash
curl -X POST http://localhost:8080/api/orders \
-H "Content-Type: application/json" \
-d '{
  "items": [
    {"productId": "FAIL-ME", "quantity": 1, "price": 10.50}
  ],
  "totalPrice": 10.50
}'
```
After 3 failed retries by the Inventory Service, the message will be routed to the DLQ (`inventory.dlq`). You can inspect this queue via the RabbitMQ Management UI at `http://localhost:15672` (guest/guest).

## Key Features Implemented
- **Publish-Subscribe (Pub/Sub)**: Decoupled communication using RabbitMQ Exchanges and Queues.
- **Database-per-Service**: Isolated logical PostgreSQL databases.
- **Eventual Consistency**: The Order Service listens to downstream events to eventually update its local order status.
- **Idempotency**: All consumers use a `processed_events` table to prevent processing duplicate messages.
- **Message Durability**: RabbitMQ queues are durable, and messages are persistent.
- **Dead Letter Queues (DLQ)**: Failed messages are automatically routed to a DLQ for inspection.
