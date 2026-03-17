# WhatsApp Integration Setup Guide

This guide explains how to set up WhatsApp Business API integration for sharing resumes with clients.

## Prerequisites

1. **WhatsApp Business Account**: You need a WhatsApp Business account
2. **Meta Developer Account**: Create a developer account at [developers.facebook.com](https://developers.facebook.com)
3. **WhatsApp Business API**: Set up WhatsApp Business API through Meta for Developers

## Setup Steps

### 1. Create WhatsApp Business API App

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create a new app and select "Business" as the app type
3. Add "WhatsApp" product to your app
4. Follow the setup wizard to configure your WhatsApp Business API

### 2. Get Required Credentials

You'll need these credentials from your Meta app:

- **Access Token**: Your WhatsApp Business API access token
- **Phone Number ID**: The ID of your WhatsApp Business phone number
- **API Version**: Usually `v18.0` (latest stable version)

### 3. Configure Environment Variables

Add these variables to your `.env` file:

```env
# WhatsApp Business API Configuration
WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=your-access-token-here
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id-here
WHATSAPP_API_VERSION=v18.0
```

### 4. Test Configuration

You can test your WhatsApp configuration using the built-in test endpoint:

```bash
# Test WhatsApp configuration
curl -X POST "http://localhost:8000/api/hr/resume/test-whatsapp" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json"
```

## Features

### Resume Sharing via WhatsApp

- **Individual Sharing**: Share single resumes with clients via WhatsApp
- **Bulk Sharing**: Share multiple resumes at once
- **Formatted Messages**: Professional message templates with candidate details
- **Resume Links**: Include direct links to resume files
- **Custom Messages**: Add additional notes and instructions

### Message Format

When sharing a resume, clients receive a formatted WhatsApp message like:

```
🎯 *New Candidate Profile*

👤 *Candidate:* John Doe
💼 *Position:* Software Engineer
🏢 *Company:* Tech Corp

📋 *Profile Summary:*
A qualified candidate has been identified for the Software Engineer position at Tech Corp.

📞 *Contact HR:* Jane Smith
📱 *Phone:* +1234567890

📎 Resume: https://your-domain.com/api/hr/resume/download/resume-id

💬 Additional Notes: Please review and provide feedback

Best regards,
Jane Smith
```

## Usage

### From Resume Detail View

1. Open any resume in the detail view
2. Click "Share with Client (WhatsApp)" button
3. Fill in the recipient phone numbers and details
4. Send the WhatsApp message

### From Resume List (Bulk Sharing)

1. Select multiple resumes using checkboxes
2. Click "Share with Client (WhatsApp)" in the bulk actions bar
3. Fill in the recipient details
4. Send WhatsApp messages for all selected resumes

### Phone Number Format

- Include country code (e.g., +1 for US, +91 for India)
- Separate multiple numbers with commas
- Example: `+1234567890, +919876543210`

## Troubleshooting

### Common Issues

1. **"WhatsApp service is not enabled"**
   - Set `WHATSAPP_ENABLED=true` in your environment variables

2. **"WhatsApp configuration incomplete"**
   - Ensure all required environment variables are set
   - Verify your access token and phone number ID

3. **"Invalid phone number format"**
   - Include country code in phone numbers
   - Use international format (e.g., +1234567890)

4. **"Failed to send WhatsApp message"**
   - Check your access token validity
   - Ensure phone numbers are registered on WhatsApp
   - Verify API rate limits

### Testing

Use the test endpoint to verify your configuration:

```bash
# Replace with your actual JWT token
curl -X POST "http://localhost:8000/api/hr/resume/test-whatsapp" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Security Considerations

1. **Access Token Security**: Keep your WhatsApp access token secure
2. **Phone Number Privacy**: Only send messages to authorized recipients
3. **Rate Limits**: Respect WhatsApp API rate limits
4. **Data Protection**: Ensure compliance with data protection regulations

## Support

For WhatsApp Business API issues:
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [Meta for Developers Support](https://developers.facebook.com/support)

For application-specific issues:
- Check application logs for detailed error messages
- Verify environment variable configuration
- Test with the built-in test endpoint
