from typing import Dict, Any
from datetime import datetime
import io
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_invoice_email_html(invoice: Dict[str, Any]) -> str:
    """Generate HTML email body for invoice"""
    
    invoice_date_str = invoice.get("invoice_date", datetime.utcnow()).strftime("%d %b %Y") if isinstance(invoice.get("invoice_date"), datetime) else str(invoice.get("invoice_date", ""))
    due_date_str = invoice.get("due_date").strftime("%d %b %Y") if invoice.get("due_date") and isinstance(invoice.get("due_date"), datetime) else ""
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9fafb; }}
            .invoice-details {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .amount {{ font-size: 24px; font-weight: bold; color: #059669; }}
            .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>INVOICE</h1>
                <p>Invoice # {invoice.get('invoice_number', 'N/A')}</p>
            </div>
            <div class="content">
                <p>Dear {invoice.get('client_name', 'Customer')},</p>
                <p>Please find attached the invoice for your records.</p>
                
                <div class="invoice-details">
                    <p><strong>Invoice Number:</strong> {invoice.get('invoice_number', 'N/A')}</p>
                    <p><strong>Invoice Date:</strong> {invoice_date_str}</p>
                    {f'<p><strong>Due Date:</strong> {due_date_str}</p>' if due_date_str else ''}
                    <p><strong>Total Amount:</strong> <span class="amount">₹{invoice.get('total_amount', 0):,.2f}</span></p>
                </div>
                
                <p>If you have any questions regarding this invoice, please don't hesitate to contact us.</p>
                <p>Thank you for your business!</p>
                
                <p>Best regards,<br>
                {invoice.get('company_name', 'Invoice Department')}</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


async def generate_invoice_pdf(invoice: Dict[str, Any]) -> bytes:
    """Generate PDF invoice"""
    if not REPORTLAB_AVAILABLE:
        # Return empty bytes if reportlab is not available
        # In production, you might want to raise an exception or use an alternative library
        print("[WARNING] ReportLab not available - PDF generation skipped")
        raise Exception("ReportLab library not installed. Please install it with: pip install reportlab")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 12))
    
    # Company Information
    company_name = invoice.get('company_name', 'Your Company')
    company_info = f"""
    <b>{company_name}</b><br/>
    {invoice.get('company_address', '')}<br/>
    GSTIN: {invoice.get('company_gstin', 'N/A')}<br/>
    PAN: {invoice.get('company_pan', 'N/A')}<br/>
    Phone: {invoice.get('company_phone', 'N/A')}<br/>
    Email: {invoice.get('company_email', 'N/A')}
    """
    story.append(Paragraph(company_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Invoice Details
    invoice_date_str = invoice.get("invoice_date", datetime.utcnow()).strftime("%d %b %Y") if isinstance(invoice.get("invoice_date"), datetime) else str(invoice.get("invoice_date", ""))
    due_date_str = invoice.get("due_date").strftime("%d %b %Y") if invoice.get("due_date") and isinstance(invoice.get("due_date"), datetime) else ""
    
    invoice_details = f"""
    <b>Invoice #:</b> {invoice.get('invoice_number', 'N/A')}<br/>
    <b>Invoice Date:</b> {invoice_date_str}<br/>
    """
    if due_date_str:
        invoice_details += f"<b>Due Date:</b> {due_date_str}<br/>"
    
    story.append(Paragraph(invoice_details, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Client Information
    story.append(Paragraph("<b>Bill To:</b>", styles['Heading3']))
    client_info = f"""
    {invoice.get('client_name', 'N/A')}<br/>
    {invoice.get('client_billing_address', '')}<br/>
    GSTIN: {invoice.get('client_gstin', 'N/A')}<br/>
    PAN: {invoice.get('client_pan', 'N/A')}<br/>
    Email: {invoice.get('client_email', 'N/A')}
    """
    story.append(Paragraph(client_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Line Items Table
    data = [['#', 'Item Description', 'SAC', 'Rate', 'Qty', 'Taxable Value', 'Tax', 'Amount']]
    
    line_items = invoice.get('line_items', [])
    for idx, item in enumerate(line_items, 1):
        data.append([
            str(idx),
            item.get('item_description', ''),
            item.get('sac_code', ''),
            f"₹{item.get('rate_per_item', 0):,.2f}",
            str(item.get('quantity', 1)),
            f"₹{item.get('taxable_value', 0):,.2f}",
            f"₹{item.get('tax_amount', 0):,.2f}",
            f"₹{item.get('amount', 0):,.2f}"
        ])
    
    # Summary row
    data.append([
        '',
        '',
        '',
        '',
        '',
        f"₹{invoice.get('subtotal', 0):,.2f}",
        f"₹{invoice.get('total_tax', 0):,.2f}",
        f"₹{invoice.get('total_amount', 0):,.2f}"
    ])
    
    table = Table(data, colWidths=[0.3*inch, 2*inch, 0.6*inch, 0.7*inch, 0.4*inch, 1*inch, 0.7*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Tax Breakdown
    tax_info = f"""
    <b>Tax Breakdown:</b><br/>
    CGST ({invoice.get('cgst_rate', 9)}%): ₹{invoice.get('cgst_amount', 0):,.2f}<br/>
    SGST ({invoice.get('sgst_rate', 9)}%): ₹{invoice.get('sgst_amount', 0):,.2f}<br/>
    <b>Total Amount: ₹{invoice.get('total_amount', 0):,.2f}</b>
    """
    story.append(Paragraph(tax_info, styles['Normal']))
    
    # Bank Details
    if invoice.get('company_bank_name'):
        story.append(Spacer(1, 20))
        bank_info = f"""
        <b>Bank Details:</b><br/>
        Bank: {invoice.get('company_bank_name', '')}<br/>
        Account: {invoice.get('company_bank_account', '')}<br/>
        IFSC: {invoice.get('company_bank_ifsc', '')}<br/>
        Branch: {invoice.get('company_bank_branch', '')}
        """
        story.append(Paragraph(bank_info, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

