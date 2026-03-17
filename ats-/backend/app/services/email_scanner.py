import imaplib
import email
from email.mime.multipart import MIMEMultipart
import os
import tempfile
import asyncio
from typing import List, Dict
from app.services.storage import storage_service
from app.services.parse_store import parse_and_store
from app.utils.file_utils import get_file_extension, ALLOWED_EXTENSIONS


def _decode_str(s):
    """Decode email string"""
    if isinstance(s, bytes):
        return s.decode('utf-8', errors='ignore')
    return str(s)


async def asyncio_run_save(temp_path: str, filename: str):
    """Async wrapper for file saving"""
    return await storage_service.save_file(temp_path, filename)


async def asyncio_run_parse_and_store(temp_path: str, user_id: str, filename: str, file_url: str):
    """Async wrapper for parse and store"""
    return await parse_and_store(temp_path, user_id, filename, file_url)


async def scan_imap_and_process(
    host: str, 
    email_addr: str, 
    password: str, 
    user_id: str,
    port: int = 993,
    use_ssl: bool = True
) -> Dict:
    """Scan IMAP inbox and process resume attachments"""
    print(f"🔍 Starting IMAP scan for {email_addr} on {host}:{port}")
    
    results = {
        "processed_emails": 0,
        "extracted_attachments": 0,
        "errors": []
    }
    
    try:
        # Connect to IMAP server
        print(f"🔌 Connecting to IMAP server...")
        if use_ssl:
            mail = imaplib.IMAP4_SSL(host, port)
        else:
            mail = imaplib.IMAP4(host, port)
        print(f"✅ Connected to IMAP server")
        
        print(f"🔐 Logging in with email: {email_addr}")
        mail.login(email_addr, password)
        print(f"✅ Login successful")
        
        print(f"📁 Selecting INBOX...")
        mail.select('INBOX')
        print(f"✅ INBOX selected")
        
        # Search for unseen messages first, then fallback to unread if needed
        print(f"🔍 Searching for unseen messages...")
        typ, data = mail.search(None, 'UNSEEN')
        
        if typ != 'OK':
            error_msg = "Failed to search emails"
            print(f"❌ {error_msg}")
            results["errors"].append(error_msg)
            return results
        
        email_ids = data[0].split()
        
        # If no unseen emails, try to find unread emails (for emails that were read but not processed)
        if len(email_ids) == 0:
            print(f"📧 No unseen emails found, checking for unread emails...")
            typ, data = mail.search(None, 'UNREAD')
            if typ == 'OK':
                email_ids = data[0].split()
                print(f"📧 Found {len(email_ids)} unread emails")
            else:
                print(f"📧 No unread emails found either")
        else:
            print(f"📧 Found {len(email_ids)} unseen emails")
        
        results["processed_emails"] = len(email_ids)
        
        for email_id in email_ids:
            try:
                print(f"📨 Processing email ID: {email_id}")
                # Fetch email
                typ, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if typ != 'OK':
                    print(f"❌ Failed to fetch email {email_id}")
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                print(f"📧 Email subject: {email_message.get('subject', 'No subject')}")
                
                # Process attachments
                attachment_count = 0
                for part in email_message.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        attachment_count += 1
                        
                        if not filename:
                            print(f"⚠️ Attachment {attachment_count} has no filename")
                            continue
                        
                        filename = _decode_str(filename)
                        file_ext = get_file_extension(filename)
                        print(f"📎 Attachment {attachment_count}: {filename} (ext: {file_ext})")
                        
                        # Check if it's a resume file
                        if file_ext in ALLOWED_EXTENSIONS:
                            print(f"✅ Resume file detected: {filename}")
                            try:
                                # Save attachment to temp file
                                content = part.get_payload(decode=True)
                                
                                with tempfile.NamedTemporaryFile(
                                    delete=False, 
                                    suffix=file_ext
                                ) as temp_file:
                                    temp_file.write(content)
                                    temp_path = temp_file.name
                                
                                print(f"💾 Saved to temp file: {temp_path}")
                                
                                # Save to storage and parse resume (async)
                                print(f"☁️ Saving to storage...")
                                file_url = await asyncio_run_save(temp_path, filename)
                                print(f"✅ File saved to storage: {file_url}")
                                
                                # Parse and store resume
                                print(f"🤖 Parsing resume with AI...")
                                await asyncio_run_parse_and_store(
                                    temp_path, user_id, filename, file_url
                                )
                                print(f"✅ Resume parsed and stored")
                                
                                results["extracted_attachments"] += 1
                                
                            except Exception as e:
                                error_msg = f"Failed to process {filename}: {str(e)}"
                                print(f"❌ {error_msg}")
                                results["errors"].append(error_msg)
                        else:
                            print(f"⚠️ Skipping non-resume file: {filename}")
                
                if attachment_count == 0:
                    print(f"📧 No attachments found in email {email_id}")
                
                # Mark email as seen
                mail.store(email_id, '+FLAGS', '\\Seen')
                print(f"✅ Marked email {email_id} as seen")
                
            except Exception as e:
                error_msg = f"Failed to process email {email_id}: {str(e)}"
                print(f"❌ {error_msg}")
                results["errors"].append(error_msg)
        
        print(f"🔚 Logging out from IMAP server")
        mail.logout()
        print(f"✅ Logout successful")
        
    except Exception as e:
        error_msg = f"IMAP connection error: {str(e)}"
        print(f"❌ {error_msg}")
        results["errors"].append(error_msg)
    
    print(f"📊 Scan completed. Results: {results}")
    return results
