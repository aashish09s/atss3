import smtplib
import asyncio
import aiohttp
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr
from typing import Optional
from bson import ObjectId
from app.core.config import settings


async def send_email(
    to_email: str, 
    subject: str, 
    body: str, 
    is_html: bool = False,
    from_name: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None
):
    """
    Send email using either Microsoft 365 or SMTP based on configuration
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        is_html: Whether body is HTML (default: False)
        from_name: Custom sender name (e.g., "John Doe")
        from_email: Custom sender email (e.g., "john.doe@company.com")
        reply_to: Reply-to email address (defaults to from_email if not specified)
    """
    try:
        # Check if Microsoft 365 is enabled
        if settings.use_microsoft365:
            print(f"[INFO] Using Microsoft 365 service for email to {to_email}")
            from app.services.microsoft365_email_service import microsoft365_service
            
            # Use Microsoft 365 service
            result = await microsoft365_service.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
                from_name=from_name,
                from_email=from_email,
                reply_to=reply_to
            )
            
            if result:
                print(f"[SUCCESS] Email sent successfully via Microsoft 365 to {to_email}")
                if from_name and from_email:
                    print(f"Sent from: {from_name} <{from_email}>")
                else:
                    print(f"Sent from: {settings.microsoft_sender_email}")
                return True
            else:
                raise Exception("Failed to send email via Microsoft 365")
        
        else:
            # Use traditional SMTP
            print(f"[INFO] Using SMTP service for email to {to_email}")
            
            def _send():
                # Create message
                msg = MIMEMultipart()
                
                # Set custom sender information
                # Only use custom email if it's provided AND valid, otherwise use SMTP settings
                if from_name and from_email and '@' in from_email:
                    # Use custom sender name and email
                    msg['From'] = formataddr((from_name, from_email))
                    # Set Reply-To to the custom email
                    msg['Reply-To'] = reply_to or from_email
                    print(f"[INFO] Using custom sender: {from_name} <{from_email}>")
                else:
                    # Fallback to default SMTP settings
                    msg['From'] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
                    msg['Reply-To'] = reply_to or settings.smtp_from_email
                    if from_name:
                        print(f"[INFO] Using SMTP sender with custom name: {from_name} (email: {settings.smtp_from_email})")
                    else:
                        print(f"[INFO] Using default SMTP sender: {settings.smtp_from_name} <{settings.smtp_from_email}>")
                
                msg['To'] = to_email
                msg['Subject'] = subject
                
                # Add body
                msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
                
                # Connect and send
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send)
            
            print(f"[SUCCESS] Email sent successfully via SMTP to {to_email}")
            if from_name and from_email:
                print(f"Sent from: {from_name} <{from_email}>")
            else:
                print(f"Sent from: {settings.smtp_from_name} <{settings.smtp_from_email}>")
            return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email to {to_email}: {str(e)}")
        raise


async def send_email_with_attachment(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False,
    from_name: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
    resume_id: Optional[str] = None,
    attach_resume: bool = False,
    attach_pdf: Optional[bytes] = None,
    pdf_filename: Optional[str] = None
):
    """Send email with optional PDF resume attachment"""
    try:
        if settings.use_microsoft365:
            # Use Microsoft 365 service
            print(f"[INFO] Using Microsoft 365 service for email with attachment to {to_email}")
            from app.services.microsoft365_email_service import Microsoft365EmailService
            
            ms365_service = Microsoft365EmailService()
            success = await ms365_service.send_email_with_attachment(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=is_html,
                from_name=from_name,
                from_email=from_email,
                resume_id=resume_id,
                attach_resume=attach_resume
            )
            
            if success:
                print(f"[SUCCESS] Email with attachment sent successfully via Microsoft 365 to {to_email}")
                return True
            else:
                raise Exception("Failed to send email via Microsoft 365")
        
        else:
            # Use traditional SMTP with attachment
            print(f"[INFO] Using SMTP service for email with attachment to {to_email}")
            
            # First, get the resume data and file
            file_data = None
            filename = 'resume.pdf'
            
            # Check if direct PDF attachment is provided
            if attach_pdf and pdf_filename:
                file_data = attach_pdf
                filename = pdf_filename
                print(f"[INFO] Using provided PDF attachment: {pdf_filename}")
            elif attach_resume and resume_id:
                try:
                    from app.db.mongo import get_db
                    
                    # Get resume file from database
                    db = await get_db()
                    resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
                    
                    if resume and resume.get('file_url'):
                        file_url = resume['file_url']
                        filename = resume.get('filename', 'resume.pdf')
                        
                        # Download file from storage
                        if file_url.startswith('http'):
                            # Try to download from HTTP URL first
                            try:
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(file_url) as response:
                                        if response.status == 200:
                                            file_data = await response.read()
                                            print(f"[SUCCESS] PDF file downloaded from URL: {filename}")
                                        else:
                                            print(f"[WARNING] Failed to download file from URL: {file_url}")
                                            # Fallback to local file
                                            file_data = None
                            except Exception as e:
                                print(f"[WARNING] HTTP download failed: {str(e)}")
                                # Fallback to local file
                                file_data = None
                        
                        # If HTTP download failed or URL is local, try local file
                        if not file_data:
                            if file_url.startswith(settings.backend_base_url):
                                # Extract local path from URL
                                local_path = file_url.replace(f"{settings.backend_base_url}/uploads/", "")
                                full_path = os.path.join(settings.local_upload_dir, local_path)
                            else:
                                # Direct path
                                full_path = file_url
                            
                            if os.path.exists(full_path):
                                with open(full_path, 'rb') as f:
                                    file_data = f.read()
                                print(f"[SUCCESS] PDF file loaded from local file: {filename}")
                            else:
                                print(f"[WARNING] Local file not found: {full_path}")
                                print(f"[WARNING] Tried path: {full_path}")
                                print(f"[WARNING] Upload dir: {settings.local_upload_dir}")
                    else:
                        print(f"[WARNING] Resume file URL not found for ID: {resume_id}")
                        # Continue without attachment - email will still be sent
                except Exception as e:
                    print(f"[WARNING] Failed to get resume file: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Continue without attachment - email will still be sent
                    file_data = None
            
            def _send_with_attachment(file_data_param, filename_param):
                # Create message
                msg = MIMEMultipart()
                
                # Set custom sender information
                # Only use custom email if it's provided AND valid, otherwise use SMTP settings
                if from_name and from_email and '@' in from_email:
                    msg['From'] = formataddr((from_name, from_email))
                    msg['Reply-To'] = reply_to or from_email
                    print(f"[INFO] Using custom sender: {from_name} <{from_email}>")
                else:
                    msg['From'] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
                    msg['Reply-To'] = reply_to or settings.smtp_from_email
                    if from_name:
                        print(f"[INFO] Using SMTP sender with custom name: {from_name} (email: {settings.smtp_from_email})")
                    else:
                        print(f"[INFO] Using default SMTP sender: {settings.smtp_from_name} <{settings.smtp_from_email}>")
                
                msg['To'] = to_email
                msg['Subject'] = subject
                
                # Add body
                msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
                
                # Add PDF attachment if we have file data
                if file_data_param:
                    try:
                        attachment = MIMEApplication(file_data_param, _subtype='pdf')
                        attachment.add_header('Content-Disposition', 'attachment', filename=filename_param)
                        attachment.add_header('Content-Type', 'application/pdf')
                        msg.attach(attachment)
                        print(f"[SUCCESS] PDF attachment added to email: {filename_param}")
                        print(f"[INFO] File size: {len(file_data_param)} bytes")
                    except Exception as e:
                        print(f"[WARNING] Failed to attach resume: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        # Continue without attachment - email will still be sent
                else:
                    if attach_resume:
                        print(f"[WARNING] No file data to attach - resume attachment requested but file not available")
                    else:
                        print(f"[INFO] No attachment requested")
                
                # Connect and send
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.send_message(msg)
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _send_with_attachment, file_data, filename)
            
            print(f"[SUCCESS] Email with attachment sent successfully via SMTP to {to_email}")
            if from_name and from_email:
                print(f"Sent from: {from_name} <{from_email}>")
            else:
                print(f"Sent from: {settings.smtp_from_name} <{settings.smtp_from_email}>")
            return True
        
    except Exception as e:
        print(f"[ERROR] Failed to send email with attachment to {to_email}: {str(e)}")
        raise


async def send_hr_email(
    to_email: str,
    subject: str,
    body: str,
    hr_name: str,
    hr_email: str,
    is_html: bool = False
):
    """
    Send email that appears to come from HR user
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        hr_name: HR user's name (e.g., "John Doe")
        hr_email: HR user's email (e.g., "john.doe@company.com")
        is_html: Whether body is HTML (default: False)
    """
    # Check if Microsoft 365 is enabled
    if settings.use_microsoft365:
        print(f"[INFO] Using Microsoft 365 service for HR email to {to_email}")
        from app.services.microsoft365_email_service import microsoft365_service
        
        # Use Microsoft 365 service for HR emails
        result = await microsoft365_service.send_hr_email(
            to_email=to_email,
            subject=subject,
            body=body,
            hr_name=hr_name,
            hr_email=hr_email,
            is_html=is_html
        )
        
        if result:
            print(f"[SUCCESS] HR email sent successfully via Microsoft 365 to {to_email}")
            print(f"Sent from: {hr_name} <{hr_email}>")
            return True
        else:
            raise Exception("Failed to send HR email via Microsoft 365")
    
    else:
        # Use traditional email service
        print(f"[INFO] Using traditional email service for HR email to {to_email}")
        return await send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=is_html,
            from_name=hr_name,
            from_email=hr_email,
            reply_to=hr_email
        )


def format_interview_details(text: str) -> str:
    """Convert plain text interview details to HTML"""
    if not text:
        return ""
    
    # Import html escaping
    from html import escape
    
    # Step 1: Process markdown-style bold (**text**) to HTML BEFORE escaping
    # Replace **text** with a placeholder, then we'll replace placeholders later
    bold_pattern = r'\*\*(.*?)\*\*'
    bold_matches = []
    placeholder_template = "___BOLD_PLACEHOLDER_{}___"
    
    def replace_bold(match):
        content = match.group(1)
        bold_matches.append(content)
        return placeholder_template.format(len(bold_matches) - 1)
    
    text = re.sub(bold_pattern, replace_bold, text)
    
    # Step 2: Escape HTML special characters
    text = escape(text)
    
    # Step 3: Replace placeholders with actual <strong> tags
    for i, bold_content in enumerate(bold_matches):
        placeholder = placeholder_template.format(i)
        text = text.replace(placeholder, f'<strong>{bold_content}</strong>')
    
    # Step 4: Convert bullet points (•) to proper list items
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            continue
            
        if line.startswith('•') or line.startswith('-'):
            if not in_list:
                formatted_lines.append('<ul style="margin: 0; padding-left: 20px;">')
                in_list = True
            content = line.lstrip('•-').strip()
            formatted_lines.append(f'<li style="margin-bottom: 8px;">{content}</li>')
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<p style="margin: 0 0 15px 0;">{line}</p>')
    
    if in_list:
        formatted_lines.append('</ul>')
    
    return ''.join(formatted_lines) if formatted_lines else text


async def send_interview_email(
    to_email: str,
    candidate_name: str,
    interview_details: str,
    hr_name: str,
    hr_email: str,
    company_name: str = "Your Company",
    subject: Optional[str] = None,
    virtual_interview_link: Optional[str] = None
):
    """
    Send interview invitation email
    
    Args:
        to_email: Candidate's email address
        candidate_name: Candidate's name
        interview_details: Interview details (date, time, location, etc.)
        hr_name: HR user's name
        hr_email: HR user's email
        company_name: Company name
    """
    print(f"[DEBUG] send_interview_email called with:")
    print(f"  to_email: {to_email}")
    print(f"  candidate_name: {candidate_name}")
    print(f"  hr_name: {hr_name}")
    print(f"  hr_email: {hr_email}")
    print(f"  company_name: {company_name}")
    print(f"  virtual_interview_link: {virtual_interview_link}")
    
    if not subject:
        subject = f"Interview Invitation - {company_name}"

    # Format interview details to HTML
    formatted_interview_details = format_interview_details(interview_details)

    # Beautiful HTML template for interview emails with properly formatted interview details
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interview Invitation</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            .header p {{
                margin: 0;
                font-size: 18px;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 20px;
                color: #2d3748;
                margin-bottom: 25px;
                font-weight: 500;
            }}
            .intro {{
                font-size: 16px;
                color: #4a5568;
                margin-bottom: 30px;
                line-height: 1.7;
            }}
            .details-section {{
                background: #f7fafc;
                border-left: 4px solid #667eea;
                padding: 25px;
                margin: 30px 0;
                border-radius: 8px;
            }}
            .details-section h3 {{
                margin: 0 0 20px 0;
                color: #2d3748;
                font-size: 20px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .detail-item {{
                display: flex;
                margin-bottom: 15px;
                align-items: flex-start;
                padding: 12px 0;
                border-bottom: 1px solid #e2e8f0;
            }}
            .detail-item:last-child {{
                border-bottom: none;
            }}
            .detail-label {{
                font-weight: 600;
                color: #4a5568;
                min-width: 140px;
                margin-right: 20px;
                font-size: 15px;
            }}
            .detail-value {{
                color: #2d3748;
                flex: 1;
                font-size: 15px;
                line-height: 1.5;
            }}
            .detail-icon {{
                width: 20px;
                height: 20px;
                margin-right: 10px;
                color: #667eea;
            }}
            .expectations {{
                background: #edf2f7;
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
            }}
            .expectations h3 {{
                margin: 0 0 20px 0;
                color: #2d3748;
                font-size: 20px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .expectations ul {{
                margin: 0;
                padding-left: 20px;
            }}
            .expectations li {{
                margin-bottom: 12px;
                color: #4a5568;
                font-size: 15px;
                line-height: 1.6;
            }}
            .next-steps {{
                background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                border-left: 4px solid #38b2ac;
            }}
            .next-steps h4 {{
                margin: 0 0 15px 0;
                color: #2c7a7b;
                font-size: 18px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .next-steps p {{
                margin: 0;
                color: #285e61;
                font-size: 15px;
                line-height: 1.6;
            }}
            .contact-info {{
                border-top: 2px solid #e2e8f0;
                padding-top: 25px;
                margin-top: 30px;
            }}
            .contact-info p {{
                margin: 0 0 8px 0;
                color: #4a5568;
            }}
            .hr-name {{
                color: #667eea;
                font-weight: 600;
                font-size: 18px;
            }}
            .footer {{
                background: #2d3748;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 14px;
            }}
            .footer p {{
                margin: 0;
                opacity: 0.8;
            }}
            .highlight {{
                color: #667eea;
                font-weight: 600;
            }}
            .interview-details-content {{
                background: white;
                border-radius: 6px;
                padding: 20px;
                margin-top: 15px;
                border: 1px solid #e2e8f0;
            }}
            .interview-details-content p {{
                margin: 0 0 15px 0;
                color: #4a5568;
                font-size: 15px;
                line-height: 1.6;
            }}
            .interview-details-content strong {{
                color: #2d3748;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Interview Invitation</h1>
                <p>{company_name}</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Dear <span class="highlight">{candidate_name}</span>,
                </div>
                
                <div class="intro">
                    Thank you for your interest in joining our team at <span class="highlight">{company_name}</span>. 
                    We are pleased to invite you for an interview to discuss your background, skills, and how you can contribute to our organization.
                </div>
                
                <div class="details-section">
                    <h3>📅 Interview Details</h3>
                    <div class="interview-details-content">
                        {formatted_interview_details}
                    </div>
                </div>
                
                ''' + (f'''
                <div class="next-steps" style="background: linear-gradient(135deg, #e6f3ff 0%, #cce7ff 100%); border-left: 4px solid #667eea;">
                    <h4>🔗 Join Virtual Interview</h4>
                    <p style="margin-bottom: 15px;">
                        Please use the following link to join the virtual interview:
                    </p>
                    <p style="margin: 0;">
                        <a href="{virtual_interview_link}" style="color: #667eea; text-decoration: none; font-weight: 600; font-size: 16px; word-break: break-all;">{virtual_interview_link}</a>
                    </p>
                </div>
                ''' if virtual_interview_link else '') + '''
                
                <div class="expectations">
                    <h3>✨ What to Expect</h3>
                    <ul>
                        <li>Discussion about your experience and skills</li>
                        <li>Questions about your career goals and motivation</li>
                        <li>Opportunity for you to ask questions about the role and company</li>
                        <li>Discussion about next steps</li>
                    </ul>
                </div>
                
                <div class="next-steps">
                    <h4>🚀 Next Steps</h4>
                    <p>
                        Please let us know your availability for the coming week, and we will schedule the interview 
                        at a convenient time for you. If you have any questions or need to reschedule, 
                        please don't hesitate to contact us.
                    </p>
                </div>
                
                <div class="contact-info">
                    <p><strong>Best regards,</strong></p>
                    <p class="hr-name">{hr_name}</p>
                    <p>HR Team</p>
                    <p>{company_name}</p>
                    <p>📧 {hr_email}</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This invitation is confidential and valid for 7 days from the date of issuance.</p>
                <p>Thank you for considering this opportunity with us!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Use safer logging that won't fail on Unicode characters
    try:
        print(f"[DEBUG] Generated email body:")
        print(f"  Subject: {subject[:50]}...")  # Truncate to avoid encoding issues
        print(f"  Body length: {len(body)} characters")
    except Exception:
        pass  # Ignore logging errors
    
    print(f"[DEBUG] Calling send_hr_email...")
    result = await send_hr_email(
        to_email=to_email,
        subject=subject,
        body=body,
        hr_name=hr_name,
        hr_email=hr_email,
        is_html=True  # Set this to True since interview_details may contain HTML
    )
    
    print(f"[DEBUG] send_hr_email completed successfully")
    return result


async def send_offer_letter_email(
    to_email: str,
    candidate_name: str,
    offer_details: str,
    hr_name: str,
    hr_email: str,
    company_name: str = "Your Company",
    subject: Optional[str] = None,
    is_html: bool = True
):
    """
    Send offer letter email
    
    Args:
        to_email: Candidate's email address
        candidate_name: Candidate's name
        offer_details: Offer details (position, salary, start date, etc.)
        hr_name: HR user's name
        hr_email: HR user's email
        company_name: Company name
    """
    if not subject:
        subject = f"Offer Letter - {company_name}"
    
    # If offer_details is already HTML, use it directly, otherwise wrap in template
    if is_html and offer_details:
        # Use the provided HTML directly
        body = offer_details
    else:
        # Beautiful HTML template for offer letter emails
        body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offer Letter</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #059669 0%, #10b981 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            .header p {{
                margin: 0;
                font-size: 18px;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 20px;
                color: #2d3748;
                margin-bottom: 25px;
                font-weight: 500;
            }}
            .intro {{
                font-size: 16px;
                color: #4a5568;
                margin-bottom: 30px;
                line-height: 1.7;
            }}
            .offer-details {{
                background: #f0fdf4;
                border-left: 4px solid #059669;
                padding: 25px;
                margin: 30px 0;
                border-radius: 8px;
            }}
            .offer-details h3 {{
                margin: 0 0 20px 0;
                color: #166534;
                font-size: 20px;
                font-weight: 600;
            }}
            .offer-content {{
                background: #f7fafc;
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                border: 1px solid #e2e8f0;
            }}
            .next-steps {{
                background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                border-left: 4px solid #3b82f6;
            }}
            .next-steps h4 {{
                margin: 0 0 15px 0;
                color: #1e40af;
                font-size: 18px;
                font-weight: 600;
            }}
            .next-steps p {{
                margin: 0;
                color: #1e3a8a;
                font-size: 15px;
                line-height: 1.6;
            }}
            .contact-info {{
                border-top: 2px solid #e2e8f0;
                padding-top: 25px;
                margin-top: 30px;
            }}
            .contact-info p {{
                margin: 0 0 8px 0;
                color: #4a5568;
            }}
            .hr-name {{
                color: #059669;
                font-weight: 600;
                font-size: 18px;
            }}
            .footer {{
                background: #2d3748;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 14px;
            }}
            .footer p {{
                margin: 0;
                opacity: 0.8;
            }}
            .highlight {{
                color: #059669;
                font-weight: 600;
            }}
            .congratulations {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                border-left: 4px solid #f59e0b;
                text-align: center;
            }}
            .congratulations h3 {{
                margin: 0 0 15px 0;
                color: #92400e;
                font-size: 24px;
                font-weight: 600;
            }}
            .congratulations p {{
                margin: 0;
                color: #78350f;
                font-size: 16px;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Offer Letter</h1>
                <p>{company_name}</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Dear <span class="highlight">{candidate_name}</span>,
                </div>
                
                <div class="congratulations">
                    <h3>🎊 Congratulations!</h3>
                    <p>We are delighted to offer you a position at <span class="highlight">{company_name}</span>!</p>
                </div>
                
                <div class="intro">
                    After careful consideration of your application and interview performance, 
                    we are excited to welcome you to our team. We believe your skills and experience 
                    will be a valuable addition to our organization.
                </div>
                
                <div class="offer-details">
                    <h3>📋 Offer Details</h3>
                    {offer_details}
                </div>
                
                <div class="offer-content">
                    <h3>📄 Complete Offer Information</h3>
                    <p>
                        Please review the complete offer details above. This offer includes all terms and conditions 
                        of employment, including compensation, benefits, and start date.
                    </p>
                </div>
                
                <div class="next-steps">
                    <h4>🚀 Next Steps</h4>
                    <p>
                        Please review the offer and let us know if you have any questions or need clarification 
                        on any terms. We look forward to your response and to having you join our team!
                    </p>
                </div>
                
                <div class="contact-info">
                    <p><strong>Best regards,</strong></p>
                    <p class="hr-name">{hr_name}</p>
                    <p>HR Team</p>
                    <p>{company_name}</p>
                    <p>📧 {hr_email}</p>
                </div>
            </div>
            
            <div class="footer">
                <p>This offer is confidential and valid for 7 days from the date of issuance.</p>
                <p>We look forward to welcoming you to our team!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_hr_email(
        to_email=to_email,
        subject=subject,
        body=body,
        hr_name=hr_name,
        hr_email=hr_email,
        is_html=True  # Set this to True since offer_details contains HTML
    )


async def send_onboarding_email(
    to_email: str,
    candidate_name: str,
    onboarding_details: str,
    hr_name: str,
    hr_email: str,
    company_name: str = "Your Company",
    onboarding_url: Optional[str] = None
):
    """
    Send candidate onboarding email
    
    Args:
        to_email: Candidate's email address
        candidate_name: Candidate's name
        onboarding_details: Onboarding instructions and details
        hr_name: HR user's name
        hr_email: HR user's email
        company_name: Company name
    """
    subject = f"Welcome to {company_name} - Onboarding Information"
    
    # Beautiful HTML template for onboarding emails
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to {company_name}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f8f9fa;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            .header p {{
                margin: 0;
                font-size: 18px;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .greeting {{
                font-size: 20px;
                color: #2d3748;
                margin-bottom: 25px;
                font-weight: 500;
            }}
            .welcome {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                border-left: 4px solid #f59e0b;
                text-align: center;
            }}
            .welcome h3 {{
                margin: 0 0 15px 0;
                color: #92400e;
                font-size: 24px;
                font-weight: 600;
            }}
            .welcome p {{
                margin: 0;
                color: #78350f;
                font-size: 16px;
                line-height: 1.6;
            }}
            .onboarding-details {{
                background: #f0f9ff;
                border-left: 4px solid #0ea5e9;
                padding: 25px;
                margin: 30px 0;
                border-radius: 8px;
            }}
            .onboarding-details h3 {{
                margin: 0 0 20px 0;
                color: #0c4a6e;
                font-size: 20px;
                font-weight: 600;
            }}
            .next-steps {{
                background: linear-gradient(135deg, #dcfce7 0%, #86efac 100%);
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                border-left: 4px solid #16a34a;
            }}
            .next-steps h4 {{
                margin: 0 0 15px 0;
                color: #15803d;
                font-size: 18px;
                font-weight: 600;
            }}
            .next-steps p {{
                margin: 0;
                color: #166534;
                font-size: 15px;
                line-height: 1.6;
            }}
            .contact-info {{
                border-top: 2px solid #e2e8f0;
                padding-top: 25px;
                margin-top: 30px;
            }}
            .contact-info p {{
                margin: 0 0 8px 0;
                color: #4a5568;
            }}
            .hr-name {{
                color: #7c3aed;
                font-weight: 600;
                font-size: 18px;
            }}
            .footer {{
                background: #2d3748;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 14px;
            }}
            .footer p {{
                margin: 0;
                opacity: 0.8;
            }}
            .highlight {{
                color: #7c3aed;
                font-weight: 600;
            }}
            .onboarding-button {{
                display: inline-block;
                background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
                color: white;
                padding: 18px 36px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                margin: 25px 0;
                text-align: center;
                box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
                transition: all 0.3s ease;
            }}
            .onboarding-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
            }}
            .button-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .warning {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
            }}
            .warning strong {{
                color: #92400e;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎊 Welcome to the Team!</h1>
                <p>{company_name}</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Dear <span class="highlight">{candidate_name}</span>,
                </div>
                
                <div class="welcome">
                    <h3>🎉 Congratulations!</h3>
                    <p>Welcome to <span class="highlight">{company_name}</span>! We're excited to have you join our team.</p>
                </div>
                
                <div class="onboarding-details">
                    <h3>📋 Onboarding Information</h3>
                    {onboarding_details}
                </div>
                
                {f'''
                <div class="button-container">
                    <a href="{onboarding_url}" class="onboarding-button">🚀 Complete Your Onboarding</a>
                </div>
                
                <div class="warning">
                    <strong>⏰ Important:</strong> This link is valid for <strong>24 hours only</strong>. 
                    Please complete your onboarding within this timeframe.
                </div>
                ''' if onboarding_url else ''}
                
                <div class="next-steps">
                    <h4>🚀 Getting Started</h4>
                    <p>
                        We're here to support you every step of the way during your onboarding process. 
                        If you have any questions or need assistance, please don't hesitate to reach out to me.
                    </p>
                </div>
                
                <div class="contact-info">
                    <p><strong>Best regards,</strong></p>
                    <p class="hr-name">{hr_name}</p>
                    <p>HR Team</p>
                    <p>{company_name}</p>
                    <p>📧 {hr_email}</p>
                </div>
            </div>
            
            <div class="footer">
                <p>We look forward to seeing you thrive in your new role!</p>
                <p>Welcome aboard! 🚀</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    print(f"[DEBUG] Generated onboarding email:")
    print(f"  Subject: {subject}")
    print(f"  Body length: {len(body)} characters")
    print(f"  Is HTML: True")
    
    print(f"[DEBUG] Calling send_hr_email...")
    result = await send_hr_email(
        to_email=to_email,
        subject=subject,
        body=body,
        hr_name=hr_name,
        hr_email=hr_email,
        is_html=True  # Onboarding email body is HTML
    )
    
    print(f"[DEBUG] send_hr_email completed successfully")
    return result
