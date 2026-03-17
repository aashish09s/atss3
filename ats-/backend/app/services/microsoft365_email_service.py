import msal
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings
import asyncio


class Microsoft365EmailService:
    """Microsoft 365 Email Service using OAuth 2.0"""
    
    def __init__(self):
        self.client_id = settings.microsoft_client_id
        self.client_secret = settings.microsoft_client_secret
        self.tenant_id = settings.microsoft_tenant_id
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        
        # Initialize MSAL application
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        # Cache for access tokens
        self._access_token = None
        self._token_expires_at = None
    
    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        current_time = datetime.now()
        
        # Check if we have a valid token
        if (self._access_token and self._token_expires_at and 
            current_time < self._token_expires_at - timedelta(minutes=5)):
            return self._access_token
        
        # Get new token
        result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            self._access_token = result["access_token"]
            # Calculate expiration (tokens typically last 1 hour)
            expires_in = result.get("expires_in", 3600)
            self._token_expires_at = current_time + timedelta(seconds=expires_in)
            return self._access_token
        else:
            error_msg = f"Failed to acquire token: {result.get('error_description', 'Unknown error')}"
            print(f"[ERROR] {error_msg}")
            raise Exception(error_msg)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        from_name: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send email using Microsoft Graph API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default: False)
            from_name: Custom sender name
            from_email: Custom sender email (must be verified in your tenant)
            reply_to: Reply-to email address
        """
        try:
            # Get access token
            access_token = self._get_access_token()
            
            # Prepare email data
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if is_html else "Text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            # Set sender if specified
            if from_name and from_email:
                email_data["message"]["from"] = {
                    "emailAddress": {
                        "name": from_name,
                        "address": from_email
                    }
                }
            
            # Set reply-to if specified
            if reply_to:
                email_data["message"]["replyTo"] = [
                    {
                        "emailAddress": {
                            "address": reply_to
                        }
                    }
                ]
                print(f"[DEBUG] Setting reply-to to: {reply_to}")
            else:
                print(f"[DEBUG] No reply-to specified")
            
            # Send email using Microsoft Graph API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Use the user's email as sender if specified, otherwise use default
            sender_email = from_email or settings.microsoft_sender_email
            endpoint = f"{self.graph_endpoint}/users/{sender_email}/sendMail"
            
            # Debug: Print email data being sent
            print(f"[DEBUG] Sending email via Microsoft Graph API:")
            print(f"  Endpoint: {endpoint}")
            print(f"  From: {from_name} <{from_email}>")
            print(f"  Reply-To: {reply_to}")
            print(f"  Subject: {subject}")
            print(f"  To: {to_email}")
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=email_data
            )
            
            if response.status_code == 202:  # 202 Accepted is success for Graph API
                print(f"[SUCCESS] Email sent successfully to {to_email}")
                if from_name and from_email:
                    print(f"Sent from: {from_name} <{from_email}>")
                else:
                    print(f"Sent from: {sender_email}")
                return True
            else:
                error_msg = f"Failed to send email: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] Response headers: {dict(response.headers)}")
                # Try to parse error details from response
                try:
                    error_data = response.json()
                    print(f"[ERROR] Error details: {error_data}")
                except:
                    pass
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"[ERROR] Error sending email to {to_email}: {str(e)}")
            return False
    
    async def send_hr_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        hr_name: str,
        hr_email: str,
        is_html: bool = False
    ) -> bool:
        """
        Send email that appears to come from HR user
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            hr_name: HR user's name
            hr_email: HR user's email (for reply-to, not sender)
            is_html: Whether body is HTML
        """
        try:
            # For Microsoft 365, we'll use the configured sender email but set reply-to to HR email
            # and show the HR name instead of "no-reply"
            print(f"[DEBUG] Sending HR email via Microsoft 365:")
            print(f"  HR Name: {hr_name}")
            print(f"  HR Email: {hr_email}")
            print(f"  To: {to_email}")
            print(f"  Subject: {subject}")
            
            # Use the configured Microsoft sender email as the "from" address
            # but set the HR email as reply-to and use HR name in the email body
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
                from_name=hr_name,  # Show HR name as sender
                from_email=settings.microsoft_sender_email,  # Use configured Microsoft sender
                reply_to=hr_email  # Set reply-to to HR email so replies go to HR
            )
        except Exception as e:
            print(f"[ERROR] Error in send_hr_email: {str(e)}")
            # Fallback: try to send without custom sender info
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html
            )

    async def send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False,
        from_name: Optional[str] = None,
        from_email: Optional[str] = None,
        resume_id: Optional[str] = None,
        attach_resume: bool = False
    ) -> bool:
        """Send email with optional PDF resume attachment via Microsoft 365"""
        try:
            # Get access token
            access_token = self._get_access_token()
            
            # Prepare email data
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "html" if is_html else "text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            # Add PDF attachment if requested
            if attach_resume and resume_id:
                try:
                    from app.db.mongo import get_db
                    from bson import ObjectId
                    import aiohttp
                    import base64
                    
                    # Get resume file from database
                    db = await get_db()
                    resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
                    
                    if resume and resume.get('file_url'):
                        file_url = resume['file_url']
                        filename = resume.get('filename', 'resume.pdf')
                        
                        # Download file from storage
                        if file_url.startswith('http'):
                            # Remote file (S3 or other HTTP storage)
                            async with aiohttp.ClientSession() as session:
                                async with session.get(file_url) as response:
                                    if response.status == 200:
                                        file_data = await response.read()
                                        # Encode file data as base64
                                        file_data_b64 = base64.b64encode(file_data).decode('utf-8')
                                        
                                        # Add attachment to email data
                                        email_data["message"]["attachments"] = [
                                            {
                                                "@odata.type": "#microsoft.graph.fileAttachment",
                                                "name": filename,
                                                "contentType": "application/pdf",
                                                "contentBytes": file_data_b64
                                            }
                                        ]
                                        print(f"[SUCCESS] PDF attachment added to Microsoft 365 email: {filename}")
                                    else:
                                        print(f"[WARNING] Failed to download file from URL: {file_url}")
                        else:
                            print(f"[WARNING] Local file attachment not supported for Microsoft 365")
                except Exception as e:
                    print(f"[WARNING] Failed to attach resume to Microsoft 365 email: {str(e)}")
            
            # Send email via Microsoft Graph API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.graph_endpoint}/users/{settings.microsoft_sender_email}/sendMail",
                headers=headers,
                json=email_data
            )
            
            if response.status_code == 202:  # 202 Accepted is success for Graph API
                print(f"[SUCCESS] Email with attachment sent successfully via Microsoft 365 to {to_email}")
                return True
            else:
                error_msg = f"Failed to send email with attachment: {response.status_code} - {response.text}"
                print(f"[ERROR] {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"[ERROR] Error sending email with attachment to {to_email}: {str(e)}")
            return False


# Global instance
microsoft365_service = Microsoft365EmailService()
