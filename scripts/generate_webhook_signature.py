"""Generate headers for testing the receive webhook API."""

import argparse
import hashlib
import hmac
import os
import time

DEFAULT_BODY = (
    '{"transaction_id":"txn-1001","amount":799.00,'
    '"currency":"INR","status":"success"}'
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate webhook timestamp and signature")
    parser.add_argument("--body", default=DEFAULT_BODY, help="Exact JSON body to sign")
    parser.add_argument("--event-id", default="evt-20260903-001")
    parser.add_argument(
        "--secret",
        default=os.getenv("WEBHOOK_SECRET", "local-webhook-secret"),
        help="Webhook secret, or set WEBHOOK_SECRET",
    )
    args = parser.parse_args()

    timestamp = str(int(time.time()))
    signature = hmac.new(
        args.secret.encode("utf-8"),
        f"{timestamp}.{args.body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    print(f"X-Event-Id: {args.event_id}")
    print(f"X-Webhook-Timestamp: {timestamp}")
    print(f"X-Signature: {signature}")
    print(f"Body: {args.body}")


if __name__ == "__main__":
    main()
