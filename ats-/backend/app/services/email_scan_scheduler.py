"""Lightweight email inbox scanning scheduler.

This module queues IMAP scans for linked inboxes and ensures they are
processed in the background without blocking API requests. It replaces the
previous heavy scheduler with a minimal asyncio-based loop.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from bson import ObjectId

from app.db.mongo import get_db
from app.services.crypto import decrypt_value
from app.services.email_scanner import scan_imap_and_process

# Mapping of scan_schedule value -> minimum interval between automatic scans
SCAN_INTERVALS: Dict[str, timedelta] = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}

_active_scans: Dict[str, asyncio.Task] = {}
_scheduler_task: Optional[asyncio.Task] = None


async def _run_scan_for_inbox(inbox_id: str) -> None:
    """Execute a single inbox scan if not already running."""
    if inbox_id in _active_scans:
        print(f"[EMAIL SCAN] Scan already running for inbox {inbox_id}, skipping duplicate request")
        return

    async def _scan_wrapper():
        try:
            db = await get_db()
            try:
                object_id = ObjectId(inbox_id)
            except Exception:
                print(f"[EMAIL SCAN] Invalid inbox ObjectId: {inbox_id}")
                return

            inbox = await db.email_inboxes.find_one({
                "_id": object_id,
                "is_active": True
            })

            if not inbox:
                print(f"[EMAIL SCAN] Inbox {inbox_id} not found or inactive")
                return

            try:
                password = decrypt_value(inbox["encrypted_password"])
            except Exception as decrypt_error:
                print(f"[EMAIL SCAN] Failed to decrypt password for inbox {inbox_id}: {decrypt_error}")
                return

            email_addr = inbox.get("email", "unknown")
            print(f"[EMAIL SCAN] Starting scan for {email_addr}")

            result = await scan_imap_and_process(
                host=inbox["imap_host"],
                email_addr=email_addr,
                password=password,
                user_id=inbox["user_id"],
                port=inbox.get("imap_port", 993),
                use_ssl=inbox.get("use_ssl", True)
            )

            print(f"[EMAIL SCAN] Completed scan for {email_addr}: {result}")

            # Update last scanned timestamp to now (UTC)
            try:
                await db.email_inboxes.update_one(
                    {"_id": object_id},
                    {"$set": {"last_scanned_at": datetime.now(timezone.utc)}}
                )
            except Exception as update_error:
                print(f"[EMAIL SCAN] Failed to update last_scanned_at for {email_addr}: {update_error}")

        except Exception as scan_error:
            print(f"[EMAIL SCAN] Unexpected error while scanning inbox {inbox_id}: {scan_error}")
        finally:
            _active_scans.pop(inbox_id, None)

    task = asyncio.create_task(_scan_wrapper())
    _active_scans[inbox_id] = task


def queue_scan_for_inbox(inbox_id: str) -> None:
    """Queue an inbox scan to run in the background."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    loop.create_task(_run_scan_for_inbox(inbox_id))


async def _scheduler_loop(poll_seconds: int = 900) -> None:
    """Background loop that triggers scans based on configured schedules."""
    # Give the application a brief moment to finish startup tasks
    await asyncio.sleep(5)

    while True:
        try:
            db = await get_db()
            inboxes = await db.email_inboxes.find({"is_active": True}).to_list(None)
            now = datetime.now(timezone.utc)

            for inbox in inboxes:
                inbox_id = str(inbox.get("_id"))
                schedule = inbox.get("scan_schedule", "daily")
                interval = SCAN_INTERVALS.get(schedule, SCAN_INTERVALS["daily"])
                last_scanned = inbox.get("last_scanned_at")

                if isinstance(last_scanned, datetime) and last_scanned.tzinfo is None:
                    last_scanned = last_scanned.replace(tzinfo=timezone.utc)

                should_scan = False
                if last_scanned is None:
                    should_scan = True
                else:
                    try:
                        should_scan = (now - last_scanned) >= interval
                    except Exception as diff_error:
                        print(f"[EMAIL SCHEDULER] Failed to compare timestamps for inbox {inbox_id}: {diff_error}")
                        should_scan = True

                if should_scan:
                    print(f"[EMAIL SCHEDULER] Queueing automatic scan for inbox {inbox_id}")
                    queue_scan_for_inbox(inbox_id)

        except asyncio.CancelledError:
            print("[EMAIL SCHEDULER] Scheduler task cancelled")
            raise
        except Exception as scheduler_error:
            print(f"[EMAIL SCHEDULER] Error while scheduling scans: {scheduler_error}")

        await asyncio.sleep(poll_seconds)


def start_email_scheduler() -> None:
    """Start the background scheduler if it isn't already running."""
    global _scheduler_task
    if _scheduler_task is not None and not _scheduler_task.done():
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    _scheduler_task = loop.create_task(_scheduler_loop())
    print("[EMAIL SCHEDULER] Started background scheduler")


async def stop_email_scheduler() -> None:
    """Cancel the background scheduler and any in-flight scans."""
    global _scheduler_task

    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
        print("[EMAIL SCHEDULER] Scheduler stopped")

    # Cancel any remaining active scans
    for inbox_id, task in list(_active_scans.items()):
        if not task.done():
            task.cancel()
        _active_scans.pop(inbox_id, None)
