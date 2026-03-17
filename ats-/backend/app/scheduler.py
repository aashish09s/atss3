from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from app.core.config import settings
from app.db.mongo import get_db
from app.services.crypto import decrypt_value
from app.services.email_scanner import scan_imap_and_process
import asyncio

# Global scheduler instance
scheduler = None


def configure_scheduler_from_db():
    """Configure scheduler with MongoDB job store"""
    jobstores = {
        'default': MongoDBJobStore(host=settings.mongodb_uri.split('@')[1].split('/')[0])
    }
    
    executors = {
        'default': AsyncIOExecutor()
    }
    
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    
    global scheduler
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults
    )


async def load_scheduled_jobs():
    """Load scheduled jobs from database"""
    if not scheduler:
        return
    
    try:
        db = await get_db()
        
        # Get all active email inboxes
        inboxes = await db.email_inboxes.find({"is_active": True}).to_list(None)
        
        for inbox in inboxes:
            try:
                # Decrypt password
                password = decrypt_if_needed(inbox.get("encrypted_password", ""))
                
                if not password:
                    continue
                
                # Schedule based on scan_schedule
                schedule = inbox.get("scan_schedule", "daily")
                job_id = f"scan_inbox_{inbox['_id']}"
                
                # Remove existing job if any
                try:
                    scheduler.remove_job(job_id)
                except:
                    pass
                
                # Add new job
                if schedule == "daily":
                    scheduler.add_job(
                        scan_inbox_job,
                        'cron',
                        hour=8,  # 8 AM daily
                        id=job_id,
                        args=[inbox],
                        replace_existing=True
                    )
                elif schedule == "weekly":
                    scheduler.add_job(
                        scan_inbox_job,
                        'cron',
                        day_of_week='mon',
                        hour=8,  # 8 AM every Monday
                        id=job_id,
                        args=[inbox],
                        replace_existing=True
                    )
                elif schedule == "monthly":
                    scheduler.add_job(
                        scan_inbox_job,
                        'cron',
                        day=1,
                        hour=8,  # 8 AM first day of month
                        id=job_id,
                        args=[inbox],
                        replace_existing=True
                    )
                
            except Exception as e:
                print(f"Failed to schedule job for inbox {inbox['_id']}: {str(e)}")
    
    except Exception as e:
        print(f"Failed to load scheduled jobs: {str(e)}")


def decrypt_if_needed(encrypted_value: str) -> str:
    """Safely decrypt value"""
    try:
        if encrypted_value:
            return decrypt_value(encrypted_value)
    except Exception as e:
        print(f"Decryption error: {str(e)}")
    return ""


def scan_inbox_job(inbox):
    """Job function to scan inbox"""
    try:
        password = decrypt_if_needed(inbox.get("encrypted_password", ""))
        
        if not password:
            print(f"No password for inbox {inbox['_id']}")
            return
        
        result = scan_imap_and_process(
            host=inbox["imap_host"],
            email_addr=inbox["email"],
            password=password,
            user_id=inbox["user_id"],
            port=inbox["imap_port"],
            use_ssl=inbox["use_ssl"]
        )
        
        print(f"Scheduled scan completed for {inbox['email']}: {result}")
        
        # Update last scanned time
        async def update_scan_time():
            from datetime import datetime
            db = await get_db()
            await db.email_inboxes.update_one(
                {"_id": inbox["_id"]},
                {"$set": {"last_scanned_at": datetime.utcnow()}}
            )
        
        # Run update in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(update_scan_time())
        finally:
            loop.close()
            
    except Exception as e:
        print(f"Scheduled scan error for inbox {inbox['_id']}: {str(e)}")


async def start_scheduler():
    """Start the scheduler"""
    global scheduler
    if scheduler and not scheduler.running:
        scheduler.start()
        print("Scheduler started successfully")


async def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("Scheduler shutdown successfully")
