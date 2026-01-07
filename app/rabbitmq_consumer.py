import json
import os
import time
import pika
import logging

from app.config import settings
from app import models, database

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE = os.getenv("PAYMENT_CONFIRMED_QUEUE", "payment_confirmed")

def store_notification(db, tenant_id: str, user_id, order_id, payment_id, payment_status):
    title = "Payment update"
    if str(payment_status).upper() == "PAID":
        title = "Payment successful"

    msg = f"Order {order_id} payment status: {payment_status}"

    n = models.Notification(
        user_id=str(user_id),
        type="PAYMENT_STATUS",
        title=title,
        message=msg,
        meta={
            "tenant_id": tenant_id,
            "order_id": order_id,
            "payment_id": payment_id,
            "payment_status": payment_status,
        },
    )
    db.add(n)
    db.commit()

def start_consumer():
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        heartbeat=600,
        blocked_connection_timeout=300,
        connection_attempts=10,
        retry_delay=2,
    )

    while True:
        try:
            logger.info("Connecting to RabbitMQ host=%s ...", settings.rabbitmq_host)
            connection = pika.BlockingConnection(parameters)
            break
        except Exception as e:
            logger.error("RabbitMQ not ready / DNS fail (%s). Retrying in 3s...", e)
            time.sleep(3)

    channel = connection.channel()
    channel.queue_declare(queue=settings.payment_confirmed_queue, durable=True)

    def callback(ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))

            tenant_id = payload.get("tenant_id", "public")
            order_id = payload.get("order_id")
            payment_id = payload.get("payment_id")
            payment_status = payload.get("payment_status")

            # Optional fields if you add them later
            user_id = payload.get("user_id", "unknown")
            amount = payload.get("amount")

            db = database.get_db_session(schema=tenant_id)
            try:
                title = "Payment successful" if str(payment_status).upper() == "PAID" else "Payment update"
                msg = f"Order {order_id} payment status: {payment_status}"

                meta = {
                    "tenant_id": tenant_id,
                    "order_id": order_id,
                    "payment_id": payment_id,
                    "payment_status": payment_status,
                }
                if amount is not None:
                    meta["amount"] = amount

                n = models.Notification(
                    user_id=str(user_id),
                    type="ORDER_PAID" if str(payment_status).upper() == "PAID" else "PAYMENT_STATUS",
                    title=title,
                    message=msg,
                    meta=meta,
                )
                db.add(n)
                db.commit()

                logger.info("Stored notification user=%s order=%s tenant=%s", user_id, order_id, tenant_id)
            finally:
                db.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Failed processing message (acking to avoid retry loop)")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=settings.payment_confirmed_queue, on_message_callback=callback)

    logger.info("Notification consumer started. Waiting for messages on '%s'...", settings.payment_confirmed_queue)
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()
