import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { DocumentDuplicateIcon, EyeIcon, PaintBrushIcon, PaperAirplaneIcon, XMarkIcon } from '@heroicons/react/24/outline';
import Header from '../../components/Header';
import api from '../../utils/api';

const OfferLetters = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingTemplateId, setEditingTemplateId] = useState(null);
  
  const [currentTemplate, setCurrentTemplate] = useState({
    name: '',
    theme_color: '#3B82F6',
    company_logo_url: '',
    company_name: '',
    hr_name: '',
    hr_email: '',
    hr_phone: '',
    position: '',
    department: '',
    base_salary: '',
    start_date: '',
    benefits: [''],
    additional_notes: '',
    terms_conditions: '',
    footer_text: ''
  });

  const [showPreview, setShowPreview] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [showSendModal, setShowSendModal] = useState(false);
  const [candidateEmail, setCandidateEmail] = useState('');
  const [candidateName, setCandidateName] = useState('');
  const [enableESign, setEnableESign] = useState(true);
  const [hrSignatureFile, setHrSignatureFile] = useState(null);
  const [hrStampFile, setHrStampFile] = useState(null);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/templates/');
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      alert('Failed to load templates. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const parseTemplateFromHTML = (html, themeColor) => {
    // Extract data from HTML template
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    
    // Extract company name
    const companyNameMatch = html.match(/<p[^>]*>([^<]+)<\/p>/);
    const companyName = companyNameMatch ? companyNameMatch[1].trim() : '';
    
    // Extract position
    const positionMatch = html.match(/<strong[^>]*style="color:[^"]*">([^<]+)<\/strong>/);
    const position = positionMatch ? positionMatch[1].trim() : '';
    
    // Extract HR name
    const hrNameMatch = html.match(/<p[^>]*style="[^"]*color:[^"]*theme_color[^"]*"[^>]*>([^<]+)<\/p>/);
    const hrName = hrNameMatch ? hrNameMatch[1].trim() : '';
    
    // Extract HR email
    const hrEmailMatch = html.match(/📧\s*([^\s<]+)/);
    const hrEmail = hrEmailMatch ? hrEmailMatch[1].trim() : '';
    
    // Extract HR phone
    const hrPhoneMatch = html.match(/📞\s*([^\s<]+)/);
    const hrPhone = hrPhoneMatch ? hrPhoneMatch[1].trim() : '';
    
    // Extract benefits
    const benefits = [];
    const benefitItems = doc.querySelectorAll('ul li');
    benefitItems.forEach(item => {
      const text = item.textContent.trim();
      if (text) benefits.push(text);
    });
    
    // Extract additional notes
    const notesMatch = html.match(/<p[^>]*style="[^"]*line-height:[^"]*"[^>]*>([^<]+)<\/p>/);
    const additionalNotes = notesMatch ? notesMatch[1].trim() : '';
    
    // Extract terms and conditions
    const termsMatch = html.match(/<p[^>]*style="margin: 0[^"]*">([^<]+)<\/p>/);
    const termsConditions = termsMatch ? termsMatch[1].trim() : '';
    
    // Extract base salary
    const salaryMatch = html.match(/Base Salary:[^<]*<p[^>]*>([^<]+)<\/p>/);
    const baseSalary = salaryMatch ? salaryMatch[1].trim() : '';
    
    // Extract start date
    const dateMatch = html.match(/Start Date:[^<]*<p[^>]*>([^<]+)<\/p>/);
    const startDate = dateMatch ? dateMatch[1].trim() : '';
    
    // Extract department
    const deptMatch = html.match(/Department:[^<]*<p[^>]*>([^<]+)<\/p>/);
    const department = deptMatch ? deptMatch[1].trim() : '';
    
    return {
      company_name: companyName || '',
      position: position || '',
      hr_name: hrName || '',
      hr_email: hrEmail || '',
      hr_phone: hrPhone || '',
      benefits: benefits.length > 0 ? benefits : [''],
      additional_notes: additionalNotes || '',
      terms_conditions: termsConditions || '',
      base_salary: baseSalary || '',
      start_date: startDate || '',
      department: department || '',
      theme_color: themeColor || '#3B82F6',
      company_logo_url: '',
      footer_text: ''
    };
  };

  const handleTemplateChange = (field, value) => {
    setCurrentTemplate(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleBenefitChange = (index, value) => {
    const newBenefits = [...currentTemplate.benefits];
    newBenefits[index] = value;
    setCurrentTemplate(prev => ({
      ...prev,
      benefits: newBenefits
    }));
  };

  const addBenefit = () => {
    setCurrentTemplate(prev => ({
      ...prev,
      benefits: [...prev.benefits, '']
    }));
  };

  const removeBenefit = (index) => {
    const newBenefits = currentTemplate.benefits.filter((_, i) => i !== index);
    setCurrentTemplate(prev => ({
      ...prev,
      benefits: newBenefits.length > 0 ? newBenefits : ['']
    }));
  };

  const formatCurrency = (value) => {
    if (!value) return '________';
    const numeric = Number(String(value).replace(/[^\d.-]/g, ''));
    if (!Number.isFinite(numeric)) return value;
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(numeric);
  };

  const formatDateLong = (value, includeWeekday = true) => {
    if (!value) {
      return '________';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    const options = includeWeekday
      ? { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }
      : { day: 'numeric', month: 'long', year: 'numeric' };
    return parsed.toLocaleDateString('en-IN', options);
  };

  const generateHTMLTemplate = (template = currentTemplate) => {
    const letterDate = formatDateLong(new Date().toISOString(), true);
    const startDate = formatDateLong(template.start_date, false);
    const salaryText = formatCurrency(template.base_salary);
    const positionText = template.position || '________';
    const companyNameText = template.company_name || 'Our Company';
    const benefitsList = template.benefits
      .filter((benefit) => benefit.trim() !== '')
      .map((benefit) => `<p style="margin: 4px 0;">• ${benefit}</p>`)
      .join('') || '<p style="margin: 4px 0;">• As per company policy</p>';

    return `
<div style="max-width: 720px; margin: 0 auto; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1F2937; background: #ffffff; border-radius: 12px; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08); overflow: hidden;">
  <div style="background: linear-gradient(135deg, ${template.theme_color || '#2563EB'} 0%, #1E293B 100%); color: #ffffff; padding: 36px;">
    <h1 style="margin: 0; font-size: 28px; letter-spacing: 0.5px;">Offer Letter</h1>
    <p style="margin: 8px 0 0; font-size: 16px; opacity: 0.85;">${companyNameText}</p>
  </div>
  <div style="padding: 40px 48px;">
    <p style="margin: 0 0 16px 0; font-size: 14px; color: #6B7280;">To</p>
    <p style="margin: 0 0 24px 0; font-size: 16px; font-weight: 600;">{{candidate_name}}</p>
    <p style="margin: 0 0 24px 0; font-size: 15px;">${letterDate}</p>
    <p style="margin: 0 0 24px 0; font-size: 15px;">Dear {{candidate_name}},</p>
    <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.8;">
      We are pleased to offer you the position of <strong>${positionText}</strong> at <strong>${companyNameText}</strong>, with a start date of <strong>${startDate}</strong>, under the following terms and conditions. Please sign and return a copy of this letter to confirm your acceptance of the offer.
    </p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">Position Summary</h3>
    <p style="margin: 4px 0; font-size: 15px;"><strong>Position:</strong> ${positionText}</p>
    <p style="margin: 4px 0; font-size: 15px;"><strong>Department:</strong> ${template.department || 'Assigned Department'}</p>
    <p style="margin: 4px 0; font-size: 15px;"><strong>Start Date:</strong> ${startDate}</p>
    <p style="margin: 4px 0 24px 0; font-size: 15px;"><strong>Compensation:</strong> ${salaryText} (Consolidated CTC)</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">1. Documentation</h3>
    <p style="margin: 6px 0; font-size: 15px;">As part of the onboarding process, please submit the following documents to HR within 3 days of joining:</p>
    <p style="margin: 4px 0; font-size: 15px;">a) Two passport-size photographs (originals)</p>
    <p style="margin: 4px 0; font-size: 15px;">b) Last three months’ salary slips and experience letters (if applicable)</p>
    <p style="margin: 4px 0; font-size: 15px;">c) Educational documents – X, XII, Graduation & Post-Graduation marksheets</p>
    <p style="margin: 4px 0; font-size: 15px;">d) Any one valid ID proof: Voter ID / Driver’s License / PAN Card / Passport / Ration Card</p>
    <p style="margin: 4px 0; font-size: 15px;">e) Copy of PAN & Aadhaar Card</p>
    <p style="margin: 4px 0 12px 0; font-size: 15px;">f) Bank Account Details</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">2. Duties and Work Hours</h3>
    <p style="margin: 4px 0; font-size: 15px;">
      As a ${positionText}, you will report to the Project Manager and will be responsible for achieving assigned goals and deliverables.
    </p>
    <p style="margin: 4px 0; font-size: 15px;">• Working Hours: 10:00 AM – 7:00 PM IST (1-hour break)</p>
    <p style="margin: 4px 0; font-size: 15px;">• Permitted Late Arrivals: Maximum 2 instances of 15 minutes per month; beyond this, half-day salary deduction applies.</p>
    <p style="margin: 4px 0; font-size: 15px;">• Leave Policy: 1 paid leave per month post probation.</p>
    <p style="margin: 4px 0; font-size: 15px;">• Employees are discouraged from taking leave on Fridays or Mondays unless in case of genuine emergencies; sandwich leave policy applies otherwise.</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">3. Compensation</h3>
    <p style="margin: 4px 0; font-size: 15px;">Your Consolidated Gross Compensation (CTC) will be as per Annexure.</p>
    <p style="margin: 4px 0; font-size: 15px;"><strong>a) Fixed Salary:</strong> You will receive a fixed monthly compensation of ${salaryText}, payable as per the company’s payroll schedule.</p>
    <p style="margin: 4px 0; font-size: 15px;"><strong>b) Performance & Attendance Bonus:</strong> You may be eligible for an annual performance and attendance bonus as per company policy. This bonus is discretionary and not included in the CTC.</p>
    <p style="margin: 4px 0 12px 0; font-size: 15px;"><strong>c) Incentives / Bonus Pay-out:</strong> If you resign or are terminated before the incentive or bonus disbursement date, you will not be eligible to receive it.</p>

    <h4 style="margin: 24px 0 8px; font-size: 16px; color: ${template.theme_color || '#1D4ED8'};">Perks & Benefits</h4>
    ${benefitsList}

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">4. Termination, Notice, and Conduct Obligations</h3>
    <p style="margin: 4px 0; font-size: 15px;">a) Your initial period of employment will be treated as a probation period of three (3) months from your joining date. During this period, the Company reserves the right to terminate your services with immediate effect and without prior notice. If you choose to resign during probation, you must provide a minimum of fifteen (15) days written notice.</p>
    <p style="margin: 4px 0; font-size: 15px;">b) Upon successful completion of probation, either party may terminate the employment by giving a thirty (30) day written notice or salary in lieu thereof.</p>
    <p style="margin: 4px 0; font-size: 15px;">c) If you fail to serve the required notice, issuance of relieving or experience letters will be solely at management’s discretion, and the Company may recover salary for the unserved days.</p>
    <p style="margin: 4px 0; font-size: 15px;">d) Continuous absence without approval for three (3) consecutive working days may result in automatic termination.</p>
    <p style="margin: 4px 0; font-size: 15px;">e) Your Full & Final (F&F) settlement will be processed within forty-five (45) days from your last working day or acceptance of resignation, whichever is later.</p>
    <p style="margin: 4px 0; font-size: 15px;">f) Non-Solicitation and Non-Poaching: For one (1) year following your resignation or termination, you shall not solicit or hire any employee, consultant, or contractor of ${companyNameText}.</p>
    <p style="margin: 4px 0; font-size: 15px;">g) Prohibition of Groupism and Union Activity: Formation of informal unions or collective efforts that disrupt operations will be treated as misconduct.</p>
    <p style="margin: 4px 0; font-size: 15px;">h) All company property, documents, electronic devices, and access credentials must be returned on or before your last working day.</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">5. Confidentiality, Non-Disclosure & Intellectual Property Protection</h3>
    <p style="margin: 4px 0; font-size: 15px;">a) During your employment with ${companyNameText}, you will have access to sensitive, confidential, and proprietary information.</p>
    <p style="margin: 4px 0; font-size: 15px;">b) All confidential information is the exclusive property of the Company. Unauthorized disclosure or duplication constitutes a serious breach.</p>
    <p style="margin: 4px 0; font-size: 15px;">c) You agree to use confidential information solely for the performance of your duties and to return or delete all such information upon termination.</p>
    <p style="margin: 4px 0; font-size: 15px;">d) All intellectual property developed during your employment shall be deemed the sole property of ${companyNameText}.</p>
    <p style="margin: 4px 0; font-size: 15px;">e) Any data theft or unauthorized sharing of information will lead to immediate termination and legal action.</p>
    <p style="margin: 4px 0; font-size: 15px;">f) Breach of this clause will entitle the Company to seek injunctive relief, equitable remedies, and recovery of legal costs.</p>
    <p style="margin: 4px 0; font-size: 15px;">g) This obligation of confidentiality remains in force during and after your employment.</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">6. Breach of Agreement & Legal Consequences</h3>
    <p style="margin: 4px 0; font-size: 15px;">a) Any violation of the terms outlined in this agreement constitutes a material breach.</p>
    <p style="margin: 4px 0; font-size: 15px;">b) The Company reserves the right to terminate employment, withhold payments, and initiate legal proceedings in the event of a breach.</p>
    <p style="margin: 4px 0; font-size: 15px;">c) Breach may result in civil, criminal, and equitable remedies under Indian law.</p>
    <p style="margin: 4px 0; font-size: 15px;">d) The Company may recover all legal costs and damages incurred.</p>
    <p style="margin: 4px 0; font-size: 15px;">e) Failure to enforce any provision shall not constitute a waiver of rights.</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">7. Transfer, Assignment & Reposting Policy</h3>
    <p style="margin: 4px 0; font-size: 15px;">a) The Company may transfer or assign you to any branch or project as per business requirements.</p>
    <p style="margin: 4px 0; font-size: 15px;">b) Transfers may involve changes in reporting structure or responsibilities.</p>
    <p style="margin: 4px 0; font-size: 15px;">c) Post transfer, you will be governed by policies applicable to that location or subsidiary.</p>
    <p style="margin: 4px 0; font-size: 15px;">d) Refusal to comply with a legitimate transfer order may lead to disciplinary action.</p>
    <p style="margin: 4px 0; font-size: 15px;">e) Travel and relocation expenses will be managed as per company policy.</p>
    <p style="margin: 4px 0; font-size: 15px;">f) The Company retains the right to delegate or realign work responsibilities as needed.</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">8. Annexure A: Compensation Structure</h3>
    <p style="margin: 4px 0; font-size: 15px;">Detailed compensation components will be provided separately as Annexure A.</p>
    <p style="margin: 4px 0; font-size: 15px;">Notes:</p>
    <p style="margin: 4px 0; font-size: 15px;">1. The above structure represents the consolidated compensation package as mutually agreed.</p>
    <p style="margin: 4px 0; font-size: 15px;">2. Incentives, bonuses, or benefits not explicitly mentioned remain at management’s discretion.</p>
    <p style="margin: 4px 0 16px 0; font-size: 15px;">3. Statutory deductions shall be made as per prevailing laws.</p>

    <h3 style="margin: 32px 0 12px; font-size: 17px; color: ${template.theme_color || '#1D4ED8'};">9. Signature Page</h3>
    <p style="margin: 4px 0; font-size: 15px;">I, <strong>{{candidate_name}}</strong>, have read and understood all terms and conditions mentioned in this offer letter and hereby accept the offer of employment with ${companyNameText}.</p>
    <p style="margin: 24px 0 4px 0; font-size: 15px;">Signature of Employee: ___________________________</p>
    <p style="margin: 4px 0; font-size: 15px;">Name: {{candidate_name}}</p>
    <p style="margin: 4px 0 24px 0; font-size: 15px;">Date: ___________________________</p>
    <p style="margin: 4px 0; font-size: 15px;">For and on behalf of ${companyNameText}</p>
    <p style="margin: 16px 0 4px 0; font-size: 15px;">Sincerely,</p>
    <p style="margin: 4px 0; font-size: 15px;">${template.hr_name || 'Authorised Signatory'}</p>
    <p style="margin: 4px 0; font-size: 15px;">${template.hr_title || 'Operations Manager'}</p>
    <p style="margin: 4px 0; font-size: 15px;">${companyNameText}</p>
  </div>
</div>`;
  };

  const renderPreview = (template = currentTemplate) => {
    let html = generateHTMLTemplate(template);
    html = html.replace(/\{\{candidate_name\}\}/g, 'John Doe');
    return { __html: html };
  };

  const handleViewTemplate = (template) => {
    // Try to get template data from placeholders first (preferred method)
    let templateData = {};
    if (template.placeholders && template.placeholders._template_data) {
      try {
        templateData = JSON.parse(template.placeholders._template_data);
      } catch (e) {
        console.warn('Failed to parse stored template data, falling back to HTML parsing');
      }
    }
    
    // If no stored data, parse from HTML
    if (Object.keys(templateData).length === 0) {
      templateData = parseTemplateFromHTML(template.body_html, template.theme_color);
    }
    
    setPreviewTemplate({
      ...templateData,
      name: template.name,
      theme_color: template.theme_color,
      company_logo_url: template.company_logo_url || ''
    });
    setShowPreview(true);
  };

  const handleEditTemplate = async (template) => {
    try {
      // Try to get template data from placeholders first (preferred method)
      let templateData = {};
      if (template.placeholders && template.placeholders._template_data) {
        try {
          templateData = JSON.parse(template.placeholders._template_data);
        } catch (e) {
          console.warn('Failed to parse stored template data, falling back to HTML parsing');
        }
      }
      
      // If no stored data, parse from HTML
      if (Object.keys(templateData).length === 0) {
        templateData = parseTemplateFromHTML(template.body_html, template.theme_color);
      }
      
      setCurrentTemplate({
        ...templateData,
        name: template.name,
        theme_color: template.theme_color,
        company_logo_url: template.company_logo_url || ''
      });
      setEditingTemplateId(template.id);
    } catch (error) {
      console.error('Error loading template:', error);
      alert('Failed to load template for editing. Please try again.');
    }
  };

  const handleNewTemplate = () => {
    setCurrentTemplate({
      name: '',
      theme_color: '#3B82F6',
      company_logo_url: '',
      company_name: '',
      hr_name: '',
      hr_email: '',
      hr_phone: '',
      position: '',
      department: '',
      base_salary: '',
      start_date: '',
      benefits: [''],
      additional_notes: '',
      terms_conditions: '',
      footer_text: ''
    });
    setEditingTemplateId(null);
  };

  const saveTemplate = async () => {
    if (!currentTemplate.name.trim()) {
      alert('Please enter a template name');
      return;
    }

    setSaving(true);
    try {
      const body_html = generateHTMLTemplate();
      // Store template data in placeholders for easy retrieval
      const placeholders = {
        candidate_name: '{{candidate_name}}',
        // Store all template data as JSON string for retrieval
        _template_data: JSON.stringify({
          company_name: currentTemplate.company_name,
          position: currentTemplate.position,
          department: currentTemplate.department,
          base_salary: currentTemplate.base_salary,
          start_date: currentTemplate.start_date,
          hr_name: currentTemplate.hr_name,
          hr_email: currentTemplate.hr_email,
          hr_phone: currentTemplate.hr_phone,
          benefits: currentTemplate.benefits,
          additional_notes: currentTemplate.additional_notes,
          terms_conditions: currentTemplate.terms_conditions,
          footer_text: currentTemplate.footer_text
        })
      };

      if (editingTemplateId) {
        // Update existing template
        await api.patch(`/api/templates/${editingTemplateId}`, {
          name: currentTemplate.name,
          company_logo_url: currentTemplate.company_logo_url,
          theme_color: currentTemplate.theme_color,
          body_html: body_html,
          placeholders: placeholders
        });
        alert('Template updated successfully!');
      } else {
        // Create new template
        await api.post('/api/templates/', {
          name: currentTemplate.name,
          company_logo_url: currentTemplate.company_logo_url,
          theme_color: currentTemplate.theme_color,
          body_html: body_html,
          placeholders: placeholders
        });
        alert('Template saved successfully!');
      }
      
      await fetchTemplates();
      handleNewTemplate();
    } catch (error) {
      console.error('Error saving template:', error);
      alert('Failed to save template. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSendToCandidate = async () => {
    if (!candidateEmail.trim() || !candidateName.trim()) {
      alert('Please fill in both candidate name and email');
      return;
    }

    setIsSending(true);
    
    try {
      let htmlTemplate = generateHTMLTemplate();
      htmlTemplate = htmlTemplate.replace(/\{\{candidate_name\}\}/g, candidateName);
      
      const formData = new FormData();
      formData.append('candidate_email', candidateEmail);
      formData.append('candidate_name', candidateName);
      formData.append('offer_html', htmlTemplate);
      formData.append('company_name', currentTemplate.company_name);
      formData.append('hr_name', currentTemplate.hr_name);
      formData.append('hr_email', currentTemplate.hr_email);
      if (currentTemplate.position) {
        formData.append('position_title', currentTemplate.position);
      }
      formData.append('subject', `Offer Letter - ${currentTemplate.position} at ${currentTemplate.company_name}`);
      formData.append('enable_esign', enableESign ? 'true' : 'false');
      if (hrSignatureFile) {
        formData.append('hr_signature', hrSignatureFile);
      }
      if (hrStampFile) {
        formData.append('hr_stamp', hrStampFile);
      }

      const response = await api.post('/api/hr/offer-signatures/initiate', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.status === 200) {
        const data = response.data || {};
        if (data.esign_enabled) {
          alert('Offer letter sent successfully with e-signature link!');
        } else {
          alert('Offer letter sent successfully without e-signature.');
        }
        setShowSendModal(false);
        setCandidateEmail('');
        setCandidateName('');
        setEnableESign(true);
        setHrSignatureFile(null);
        setHrStampFile(null);
      } else {
        alert(`Failed to send offer letter: ${response.data?.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error sending offer letter:', error);
      const detail = error?.response?.data?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item?.msg || '').join(', ')
        : detail || 'Failed to send offer letter. Please try again.';
      alert(message);
    } finally {
      setIsSending(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header 
          title="Offer Letter Templates" 
          subtitle="Create and manage customizable offer letter templates using our form builder"
        />
        <div className="mt-6 flex justify-center">
          <div className="spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header 
        title="Offer Letter Templates" 
        subtitle="Create and manage customizable offer letter templates using our form builder"
      />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Template Form */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Template Builder</h3>
              <button
                onClick={handleNewTemplate}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                New Template
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Basic Template Info */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900 mb-3">Basic Information</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Template Name
                    </label>
                    <input
                      type="text"
                      value={currentTemplate.name}
                      onChange={(e) => handleTemplateChange('name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter template name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Theme Color
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="color"
                        value={currentTemplate.theme_color}
                        onChange={(e) => handleTemplateChange('theme_color', e.target.value)}
                        className="w-12 h-10 border border-gray-300 rounded-lg"
                      />
                      <input
                        type="text"
                        value={currentTemplate.theme_color}
                        onChange={(e) => handleTemplateChange('theme_color', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Company Information */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900 mb-3">Company Information</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Name
                    </label>
                    <input
                      type="text"
                      value={currentTemplate.company_name}
                      onChange={(e) => handleTemplateChange('company_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter company name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company Logo URL (Optional)
                    </label>
                    <input
                      type="url"
                      value={currentTemplate.company_logo_url}
                      onChange={(e) => handleTemplateChange('company_logo_url', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="https://example.com/logo.png"
                    />
                  </div>
                </div>
              </div>

              {/* Position Details */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900 mb-3">Position Details</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Position Title
                    </label>
                    <input
                      type="text"
                      value={currentTemplate.position}
                      onChange={(e) => handleTemplateChange('position', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Software Engineer"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Department
                    </label>
                    <input
                      type="text"
                      value={currentTemplate.department}
                      onChange={(e) => handleTemplateChange('department', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., Engineering"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Base Salary
                    </label>
                    <input
                      type="text"
                      value={currentTemplate.base_salary}
                      onChange={(e) => handleTemplateChange('base_salary', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="e.g., $75,000"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={currentTemplate.start_date}
                      onChange={(e) => handleTemplateChange('start_date', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Benefits */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900 mb-3">Benefits & Perks</h4>
                <div className="space-y-2">
                  {currentTemplate.benefits.map((benefit, index) => (
                    <div key={index} className="flex space-x-2">
                      <input
                        type="text"
                        value={benefit}
                        onChange={(e) => handleBenefitChange(index, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter benefit"
                      />
                      <button
                        onClick={() => removeBenefit(index)}
                        className="px-3 py-2 text-red-600 hover:text-red-800 border border-red-300 rounded-lg hover:bg-red-50"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addBenefit}
                    className="w-full px-3 py-2 text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50 hover:border-blue-400"
                  >
                    + Add Benefit
                  </button>
                </div>
              </div>

              {/* HR Information */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900 mb-3">HR Contact Information</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      HR Representative Name
                    </label>
                    <input
                      type="text"
                      value={currentTemplate.hr_name}
                      onChange={(e) => handleTemplateChange('hr_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter HR name"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        HR Email
                      </label>
                      <input
                        type="email"
                        value={currentTemplate.hr_email}
                        onChange={(e) => handleTemplateChange('hr_email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="hr@company.com"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        HR Phone (Optional)
                      </label>
                      <input
                        type="tel"
                        value={currentTemplate.hr_phone}
                        onChange={(e) => handleTemplateChange('hr_phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        placeholder="+1 (555) 123-4567"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Additional Content */}
              <div className="border-b border-gray-200 pb-4">
                <h4 className="font-medium text-gray-900 mb-3">Additional Content</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Additional Notes
                    </label>
                    <textarea
                      value={currentTemplate.additional_notes}
                      onChange={(e) => handleTemplateChange('additional_notes', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Any additional information or personal message..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Terms & Conditions
                    </label>
                    <textarea
                      value={currentTemplate.terms_conditions}
                      onChange={(e) => handleTemplateChange('terms_conditions', e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Terms and conditions for the offer..."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Footer Text (Optional)
                    </label>
                    <textarea
                      value={currentTemplate.footer_text}
                      onChange={(e) => handleTemplateChange('footer_text', e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Additional footer message..."
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={saveTemplate}
                  disabled={saving}
                  className="btn-gradient-primary px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                >
                  {saving ? 'Saving...' : editingTemplateId ? 'Update Template' : 'Save Template'}
                </button>
                <button
                  onClick={() => {
                    setPreviewTemplate(currentTemplate);
                    setShowPreview(true);
                  }}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
                >
                  <EyeIcon className="h-5 w-5" />
                  <span>Preview</span>
                </button>
                <button
                  onClick={() => {
                    setEnableESign(true);
                    setShowSendModal(true);
                  }}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                  <span>Send to Candidate</span>
                </button>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Templates List */}
        <div>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Saved Templates</h3>
            
            {templates.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No templates saved yet. Create your first template!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: template.theme_color }}
                      ></div>
                      <div>
                        <h4 className="font-medium text-gray-900">{template.name}</h4>
                        <p className="text-sm text-gray-500">
                          Created {new Date(template.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEditTemplate(template)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Edit Template"
                      >
                        <PaintBrushIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleViewTemplate(template)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="Preview Template"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Preview Modal */}
      {showPreview && previewTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold">Template Preview - {previewTemplate.name}</h3>
                <button
                  onClick={() => {
                    setShowPreview(false);
                    setPreviewTemplate(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div dangerouslySetInnerHTML={renderPreview(previewTemplate)} />
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Send to Candidate Modal */}
      {showSendModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-xl w-full max-w-lg mx-4 flex flex-col" 
            style={{ maxHeight: '85vh' }}
          >
            {/* Header - Fixed at top */}
            <div className="flex-shrink-0 px-6 pt-6 pb-4 border-b border-gray-100">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Send Offer Letter</h3>
                <button
                  onClick={() => {
                    setShowSendModal(false);
                    setEnableESign(true);
                    setHrSignatureFile(null);
                    setHrStampFile(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>
            
            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Candidate Name *
                  </label>
                  <input
                    type="text"
                    value={candidateName}
                    onChange={(e) => setCandidateName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter candidate's full name"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Candidate Email *
                  </label>
                  <input
                    type="email"
                    value={candidateEmail}
                    onChange={(e) => setCandidateEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="candidate@email.com"
                    required
                  />
                </div>
                
                <div className="flex items-start space-x-3 border border-blue-200 bg-blue-50 rounded-lg p-4">
                  <input
                    id="enable-esign"
                    type="checkbox"
                    checked={enableESign}
                    onChange={(e) => {
                      const checked = e.target.checked;
                      setEnableESign(checked);
                      if (!checked) {
                        setHrSignatureFile(null);
                        setHrStampFile(null);
                      }
                    }}
                    className="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <div>
                    <label htmlFor="enable-esign" className="text-sm font-medium text-blue-900">
                      Enable digital acceptance & e-signature workflow
                    </label>
                    <p className="text-xs text-blue-800 mt-1">
                      When enabled, the candidate receives a secure link to view, sign, and upload their signature/stamp.
                      A signed PDF will be generated and emailed to both sides automatically.
                    </p>
                  </div>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Email Preview</h4>
                  <p className="text-sm text-blue-800">
                    <strong>Subject:</strong> Offer Letter - {currentTemplate.position} at {currentTemplate.company_name}
                  </p>
                  <p className="text-sm text-blue-800 mt-1">
                    <strong>From:</strong> {currentTemplate.hr_name} ({currentTemplate.hr_email})
                  </p>
                  <p className="text-sm text-blue-800 mt-1">
                    <strong>To:</strong> {candidateName} ({candidateEmail})
                  </p>
                </div>

                {enableESign && (
                  <div className="space-y-4 border border-blue-100 bg-blue-50/60 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900">HR Authorization Assets</h4>
                    <p className="text-xs text-blue-800">
                      Upload your pre-approved signature and optional company stamp. These will be embedded in the final signed PDF alongside the candidate&apos;s signature.
                    </p>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        HR Signature (PNG/JPG)
                      </label>
                      <input
                        type="file"
                        accept="image/png,image/jpeg"
                        onChange={(e) => setHrSignatureFile(e.target.files?.[0] || null)}
                        className="w-full text-sm text-gray-600"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        For best results, use a transparent PNG file of the official signature.
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Company Stamp (optional)
                      </label>
                      <input
                        type="file"
                        accept="image/png,image/jpeg"
                        onChange={(e) => setHrStampFile(e.target.files?.[0] || null)}
                        className="w-full text-sm text-gray-600"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Footer - Fixed at bottom */}
            <div className="flex-shrink-0 px-6 py-4 border-t border-gray-100 bg-white">
              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowSendModal(false);
                    setEnableESign(true);
                    setHrSignatureFile(null);
                    setHrStampFile(null);
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendToCandidate}
                  disabled={isSending || !candidateEmail.trim() || !candidateName.trim()}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isSending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Sending...</span>
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="h-4 w-4" />
                      <span>Send Offer Letter</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default OfferLetters;
