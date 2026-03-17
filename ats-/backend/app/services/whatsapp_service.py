"""
WhatsApp Business API Service for sending messages and sharing resumes
"""
import asyncio
import httpx
import json
from typing import Optional, Dict, Any, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.access_token = getattr(settings, 'whatsapp_access_token', None)
        self.phone_number_id = getattr(settings, 'whatsapp_phone_number_id', None)
        self.api_version = getattr(settings, 'whatsapp_api_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    async def send_message(
        self,
        to_phone: str,
        message: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message to a phone number
        
        Args:
            to_phone: Recipient phone number (with country code, no +)
            message: Message content
            message_type: Type of message (text, template, etc.)
            
        Returns:
            Dict with response data
        """
        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp credentials not configured")
            
        # Clean phone number (remove + and spaces)
        clean_phone = to_phone.replace('+', '').replace(' ', '').replace('-', '')
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": message_type,
            "text": {
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"WhatsApp message sent successfully to {clean_phone}")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp API error: {e}")
            raise Exception(f"Failed to send WhatsApp message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp message: {e}")
            raise Exception(f"Failed to send WhatsApp message: {str(e)}")
    
    async def send_resume_share_message(
        self,
        to_phone: str,
        candidate_name: str,
        position: str,
        company_name: str,
        hr_name: str,
        hr_phone: str,
        resume_url: Optional[str] = None,
        additional_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a formatted message for sharing a resume with client
        
        Args:
            to_phone: Client's phone number
            candidate_name: Name of the candidate
            position: Position being applied for
            company_name: Company name
            hr_name: HR person's name
            hr_phone: HR person's phone number
            resume_url: Optional URL to resume file
            additional_message: Optional additional message
            
        Returns:
            Dict with response data
        """
        
        # Format the message
        message = f"""🎯 *New Candidate Profile*

👤 *Candidate:* {candidate_name}
💼 *Position:* {position}
🏢 *Company:* {company_name}

📋 *Profile Summary:*
A qualified candidate has been identified for the {position} position at {company_name}. 

📞 *Contact HR:* {hr_name}
📱 *Phone:* {hr_phone}

{f"📎 Resume: {resume_url}" if resume_url else ""}

{f"💬 Additional Notes: {additional_message}" if additional_message else ""}

Please review the candidate profile and let us know your feedback.

Best regards,
{hr_name}"""

        return await self.send_message(to_phone, message)
    
    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        template_params: List[str],
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp template message
        
        Args:
            to_phone: Recipient phone number
            template_name: Name of the approved template
            template_params: List of parameters for the template
            language_code: Language code (default: en)
            
        Returns:
            Dict with response data
        """
        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp credentials not configured")
            
        clean_phone = to_phone.replace('+', '').replace(' ', '').replace('-', '')
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": param} for param in template_params
                        ]
                    }
                ]
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"WhatsApp template message sent successfully to {clean_phone}")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp template API error: {e}")
            raise Exception(f"Failed to send WhatsApp template message: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp template message: {e}")
            raise Exception(f"Failed to send WhatsApp template message: {str(e)}")
    
    def validate_phone_number(self, phone: str) -> bool:
        """
        Basic phone number validation
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if phone number format is valid
        """
        # Remove all non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # Check if it's between 7 and 15 digits (international standard)
        return 7 <= len(clean_phone) <= 15
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for WhatsApp API
        
        Args:
            phone: Phone number to format
            
        Returns:
            Formatted phone number
        """
        # Remove all non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        
        # If it doesn't start with country code, assume it's a local number
        # You might want to modify this based on your use case
        if len(clean_phone) == 10:
            # Assume US number, add country code
            clean_phone = "1" + clean_phone
        
        return clean_phone

# Global instance
whatsapp_service = WhatsAppService()
