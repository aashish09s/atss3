import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import { 
  DocumentArrowUpIcon, 
  PaperAirplaneIcon,
  BriefcaseIcon,
  CalendarIcon,
  BuildingOfficeIcon,
  XMarkIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import api from '../../utils/api';

// Fallback when API does not return business types
const DEFAULT_BUSINESS_TYPES = [
  { code: 'third_party_payroll', name: 'Third-Party Payroll', prefix: 'tpp' },
  { code: 'payroll_mgmt', name: 'Payroll Management', prefix: 'pm' },
  { code: 'compliance_mgmt', name: 'Compliance Management', prefix: 'cm' },
  { code: 'recruitment', name: 'Recruitment', prefix: 'rc' },
  { code: 'task_mgmt', name: 'Task Management', prefix: 'tm' },
  { code: 'licensing_reg', name: 'Licensing & Registration', prefix: 'lr' },
];

const Invoice = () => {
  const [jobs, setJobs] = useState([]);
  const [invoices, setInvoices] = useState({}); // legacy map for JD rows
  const [invoiceRows, setInvoiceRows] = useState([]); // list view rows
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sendingInvoice, setSendingInvoice] = useState(null);
  const [showInvoiceForm, setShowInvoiceForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [editingInvoiceId, setEditingInvoiceId] = useState(null);
  const [wasPreviouslySent, setWasPreviouslySent] = useState(false);
  const [businessTypes, setBusinessTypes] = useState([]);
  const [formData, setFormData] = useState({
    invoice_date: '',
    due_date: '',
    business_type_code: '',
    invoice_type: 'tax', // 'tax' | 'proforma'
    calculate_tax: true, // Toggle to calculate tax or not
    company_name: '',
    company_gstin: '',
    company_pan: '',
    company_address: '',
    company_phone: '',
    company_email: '',
    company_website: '',
    company_bank_name: '',
    company_bank_account: '',
    company_bank_ifsc: '',
    company_bank_branch: '',
    client_email: '',
    client_phone: '',
    client_billing_address: '',
    client_company_name: '',
    client_gstin: '',
    client_pan: '',
    place_of_supply: '',
    line_items: [{ item_description: '', business_unique_id: '', sac_code: '998313', rate_per_item: 0, quantity: 1, tax_rate: 18 }],
    notes: '',
    terms_and_conditions: ''
  });

  useEffect(() => {
    fetchBusinessTypes();
    fetchInvoices(); // This now also fetches fulfilled jobs
  }, []);

  // When business types load, set default in form if missing
  useEffect(() => {
    if (businessTypes.length > 0 && !formData.business_type_code) {
      setFormData(prev => ({ ...prev, business_type_code: businessTypes[0].code }));
    }
  }, [businessTypes]);

  // When business type OR invoice type changes, fetch next invoice number and lock Business Unique ID
  useEffect(() => {
    const applyPrefix = async () => {
      if (!formData.business_type_code) return;
      try {
        const resp = await api.get('/api/hr/invoices/next-number', {
          params: { business_type_code: formData.business_type_code, invoice_type: formData.invoice_type || 'tax' }
        });
        const nextNum = resp.data?.invoice_number || '';
        const newItems = formData.line_items.map(li => ({ ...li, business_unique_id: nextNum }));
        setFormData(prev => ({ ...prev, line_items: newItems }));
      } catch (e) {
        // fallback format
        const bt = DEFAULT_BUSINESS_TYPES.find(b => b.code === formData.business_type_code);
        const prefix = bt?.prefix || 'id';
        const suffix = formData.invoice_type === 'proforma' ? 'p' : 't';
        const newItems = formData.line_items.map(li => ({ ...li, business_unique_id: `${prefix}-1${suffix}` }));
        setFormData(prev => ({ ...prev, line_items: newItems }));
      }
    };
    applyPrefix();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.business_type_code, formData.invoice_type]);
  const fetchBusinessTypes = async () => {
    try {
      const res = await api.get('/api/hr/business-types/');
      const list = Array.isArray(res.data) ? res.data : [];
      setBusinessTypes(list.length > 0 ? list : DEFAULT_BUSINESS_TYPES);
    } catch (e) {
      console.error('Failed to load business types, using defaults', e);
      setBusinessTypes(DEFAULT_BUSINESS_TYPES);
    }
  };


  const fetchFulfilledJobs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/hr/jds/fulfilled');
      const jobsData = response.data;
      setJobs(jobsData);
      
      // Fetch invoices for each job
      const invoiceMap = {};
      for (const job of jobsData) {
        try {
          const invoiceResponse = await api.get(`/api/hr/invoices/job/${job.id}`);
          if (invoiceResponse.data) {
            invoiceMap[job.id] = invoiceResponse.data;
          }
        } catch (err) {
          // No invoice exists for this job, that's okay
        }
      }
      setInvoices(invoiceMap);
      setError(null);
    } catch (err) {
      console.error('Error fetching fulfilled jobs:', err);
      setError('Failed to load fulfilled jobs');
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenInvoiceForm = async (job) => {
    setSelectedJob(job);
    
    // Pre-fill form with job data
    const defaultEarning = job.your_earning || job.budget_amount || 0;
    
    // Auto-select recruitment business type when creating from JD
    const recruitmentType = businessTypes.find(bt => 
      bt.code === 'recruitment' || bt.code === 'rec' || bt.name?.toLowerCase().includes('recruitment')
    ) || businessTypes.find(bt => bt.prefix === 'rec') || businessTypes[0];
    
    const selectedBusinessType = recruitmentType?.code || 'recruitment';
    
    // Fetch the next invoice number immediately for recruitment business type
    let initialUniqueId = '';
    try {
      const resp = await api.get('/api/hr/invoices/next-number', {
        params: { business_type_code: selectedBusinessType, invoice_type: 'tax' }
      });
      initialUniqueId = resp.data?.invoice_number || '';
    } catch (e) {
      // Fallback: use 'rc' prefix as per user requirement
      const prefix = 'rc';
      initialUniqueId = `${prefix}-1t`; // Default to tax invoice format
    }
    
    setFormData({
      invoice_date: job.invoice_date ? new Date(job.invoice_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
      due_date: '',
      business_type_code: selectedBusinessType,
      invoice_type: 'tax',
      calculate_tax: true,
      company_name: '',
      company_gstin: '',
      company_pan: '',
      company_address: '',
      company_phone: '',
      company_email: '',
      company_website: '',
      company_bank_name: '',
      company_bank_account: '',
      company_bank_ifsc: '',
      company_bank_branch: '',
      client_name: job.client_name || '',
      client_email: '',
      client_phone: '',
      client_billing_address: '',
      client_company_name: '',
      client_gstin: '',
      client_pan: '',
      place_of_supply: '',
      line_items: [{
        item_description: `Hiring Services for ${job.title}`,
        business_unique_id: initialUniqueId, // Pre-fill with auto-generated ID
        sac_code: '998313',
        rate_per_item: defaultEarning,
        quantity: 1,
        tax_rate: 18
      }],
      notes: '',
      terms_and_conditions: ''
    });
    
    setShowInvoiceForm(true);
  };

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Make both API calls in parallel for faster loading
      // Use /all-for-invoice endpoint to get ALL JDs (not just fulfilled ones) so they appear immediately
      const [invoicesRes, fulfilledRes] = await Promise.allSettled([
        api.get('/api/hr/invoices/'),
        api.get('/api/hr/jds/all-for-invoice')
      ]);
      
      // Get invoices (required)
      const invoices = invoicesRes.status === 'fulfilled' 
        ? (invoicesRes.value.data || [])
        : [];
      
      if (invoicesRes.status === 'rejected') {
        throw new Error('Failed to fetch invoices');
      }
      
      // Get fulfilled JDs (optional - can continue without them)
      let fulfilledJDs = [];
      if (fulfilledRes.status === 'fulfilled') {
        fulfilledJDs = fulfilledRes.value.data || [];
        // Update jobs state for use in action handlers
        setJobs(fulfilledJDs);
      } else {
        console.warn('Failed to fetch fulfilled JDs (non-critical):', fulfilledRes.reason);
        // Continue without fulfilled JDs if this fails
        fulfilledJDs = [];
      }
      
      // Create a map of JD IDs that already have invoices
      const jdsWithInvoices = new Set(invoices.filter(inv => inv.jd_id).map(inv => inv.jd_id));
      
      // Add fulfilled JDs without invoices to the list
      const jdRows = fulfilledJDs
        .filter(jd => jd && jd.id && !jdsWithInvoices.has(jd.id))
        .map(jd => ({
          id: `jd-pending-${jd.id}`, // Prefix to identify pending invoices
          jd_id: jd.id,
          jd_unique_id: jd.jd_unique_id,
          invoice_number: jd.jd_unique_id || `JD-${jd.id.slice(-6)}`, // Use JD unique ID as display
          invoice_date: jd.invoice_date ? new Date(jd.invoice_date) : new Date(),
          client_name: jd.client_name || '-',
          source: 'jd',
          status: 'pending', // Special status for pending invoice creation
          total_amount: jd.your_earning || jd.budget_amount || 0,
          created_at: jd.created_at ? new Date(jd.created_at) : new Date()
        }));
      
      // Combine invoices and pending JD invoices, sorted by date
      const allRows = [...invoices, ...jdRows].sort((a, b) => {
        try {
          const dateA = new Date(a.invoice_date || a.created_at);
          const dateB = new Date(b.invoice_date || b.created_at);
          return dateB - dateA; // Newest first
        } catch (sortError) {
          return 0; // If sorting fails, maintain original order
        }
      });
      
      setInvoiceRows(allRows);
      setError(null);
    } catch (e) {
      console.error('Failed to fetch invoices', e);
      setError('Failed to load invoices. Please try again.');
      setInvoiceRows([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDirectInvoice = () => {
    const today = new Date().toISOString().split('T')[0];
    const initBt = businessTypes[0]?.code || '';
    setSelectedJob({ id: null, jd_unique_id: null, client_name: '' });
    setEditingInvoiceId(null);
    setWasPreviouslySent(false);
    setFormData({
      invoice_date: today,
      due_date: '',
      business_type_code: initBt,
      invoice_type: 'tax',
      calculate_tax: true,
      company_name: '',
      company_gstin: '',
      company_pan: '',
      company_address: '',
      company_phone: '',
      company_email: '',
      company_website: '',
      company_bank_name: '',
      company_bank_account: '',
      company_bank_ifsc: '',
      company_bank_branch: '',
      client_name: '',
      client_email: '',
      client_phone: '',
      client_billing_address: '',
      client_company_name: '',
      client_gstin: '',
      client_pan: '',
      place_of_supply: '',
      line_items: [{ item_description: '', business_unique_id: '', sac_code: '998313', rate_per_item: 0, quantity: 1, tax_rate: 18 }],
      notes: '',
      terms_and_conditions: ''
    });
    setShowInvoiceForm(true);
  };

  const calculateInvoiceTotals = () => {
    const subtotal = formData.line_items.reduce((sum, item) => {
      const itemTotal = (item.rate_per_item || 0) * (item.quantity || 1);
      return sum + itemTotal;
    }, 0);
    
    const totalTaxRaw = formData.line_items.reduce((sum, item) => {
      const itemTotal = (item.rate_per_item || 0) * (item.quantity || 1);
      const taxRate = item.tax_rate || 18;
      const itemTax = itemTotal * (taxRate / 100);
      return sum + itemTax;
    }, 0);
    // Use calculate_tax toggle instead of invoice_type
    const totalTax = formData.calculate_tax ? totalTaxRaw : 0;
    
    const cgstRate = 9; // Half of 18%
    const sgstRate = 9;
    const cgstAmount = formData.calculate_tax ? totalTax / 2 : 0;
    const sgstAmount = formData.calculate_tax ? totalTax / 2 : 0;
    const totalAmount = subtotal + totalTax;
    
    return { subtotal, totalTax, cgstRate, sgstRate, cgstAmount, sgstAmount, totalAmount };
  };

  const handleFormChange = (field, value, index = null) => {
    if (index !== null) {
      // Update line item
      const newLineItems = [...formData.line_items];
      newLineItems[index][field] = value;
      
      // Recalculate line item amounts
      const itemTotal = (newLineItems[index].rate_per_item || 0) * (newLineItems[index].quantity || 1);
      const taxRate = newLineItems[index].tax_rate || 18;
      newLineItems[index].taxable_value = itemTotal;
      newLineItems[index].tax_amount = formData.calculate_tax ? (itemTotal * (taxRate / 100)) : 0;
      newLineItems[index].amount = itemTotal + (newLineItems[index].tax_amount || 0);
      
      setFormData(prev => ({ ...prev, line_items: newLineItems }));
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const addLineItem = () => {
    setFormData(prev => ({
      ...prev,
      line_items: [...prev.line_items, {
        item_description: '',
        business_unique_id: '',
        sac_code: '998313',
        rate_per_item: 0,
        quantity: 1,
        tax_rate: 18
      }]
    }));
  };

  const removeLineItem = (index) => {
    if (formData.line_items.length > 1) {
      setFormData(prev => ({
        ...prev,
        line_items: prev.line_items.filter((_, i) => i !== index)
      }));
    }
  };

  const handleSaveInvoice = async () => {
    try {
      // Basic validation
      if (!formData.business_type_code) {
        alert('Please select a Business Type.');
        return;
      }
      if (!formData.client_name || !formData.client_name.trim()) {
        alert('Please enter Client Name.');
        return;
      }

      const totals = calculateInvoiceTotals();
      
      const invoicePayload = {
        jd_id: selectedJob && selectedJob.id ? selectedJob.id : null,
        source: selectedJob && selectedJob.id ? 'jd' : 'direct',
        business_type_code: formData.business_type_code,
        invoice_type: formData.invoice_type,
        calculate_tax: formData.calculate_tax,
        invoice_date: new Date(formData.invoice_date).toISOString(),
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        company_name: formData.company_name,
        company_gstin: formData.company_gstin,
        company_pan: formData.company_pan,
        company_address: formData.company_address,
        company_phone: formData.company_phone,
        company_email: formData.company_email,
        company_website: formData.company_website,
        company_bank_name: formData.company_bank_name,
        company_bank_account: formData.company_bank_account,
        company_bank_ifsc: formData.company_bank_ifsc,
        company_bank_branch: formData.company_bank_branch,
        client_name: formData.client_name || selectedJob.client_name,
        client_email: formData.client_email,
        client_phone: formData.client_phone,
        client_billing_address: formData.client_billing_address,
        client_company_name: formData.client_company_name,
        client_gstin: formData.client_gstin,
        client_pan: formData.client_pan,
        place_of_supply: formData.place_of_supply,
        line_items: formData.line_items.map(item => ({
          item_description: item.item_description,
          business_unique_id: item.business_unique_id,
          sac_code: item.sac_code,
          rate_per_item: item.rate_per_item,
          quantity: item.quantity,
          taxable_value: item.taxable_value || (item.rate_per_item * item.quantity),
          tax_rate: item.tax_rate,
          tax_amount: formData.calculate_tax ? (item.tax_amount || (item.rate_per_item * item.quantity * item.tax_rate / 100)) : 0,
          amount: formData.calculate_tax ? (item.amount || (item.rate_per_item * item.quantity * (1 + item.tax_rate / 100))) : (item.rate_per_item * item.quantity)
        })),
        subtotal: totals.subtotal,
        cgst_rate: totals.cgstRate,
        sgst_rate: totals.sgstRate,
        cgst_amount: totals.cgstAmount,
        sgst_amount: totals.sgstAmount,
        total_tax: totals.totalTax,
        total_amount: totals.totalAmount,
        notes: formData.notes,
        terms_and_conditions: formData.terms_and_conditions
      };
      
      let response;
      if (editingInvoiceId) {
        // Update existing invoice
        response = await api.put(`/api/hr/invoices/${editingInvoiceId}`, invoicePayload);
        await fetchInvoices();
        setEditingInvoiceId(null);
        setWasPreviouslySent(false);
      } else {
        // Create new invoice
        response = await api.post('/api/hr/invoices/', invoicePayload);
        setInvoiceRows(prev => [response.data, ...prev]);
      }
      setShowInvoiceForm(false);
      alert('Invoice saved successfully!');
    } catch (err) {
      console.error('Error saving invoice:', err);
      alert('Failed to save invoice. Please try again.');
    }
  };

  const handleSendInvoiceFromForm = async () => {
    try {
      // Save first (update if editing, create if new)
      const invoiceId = editingInvoiceId;
      if (!invoiceId) {
        // New invoice - save first
        const before = invoiceRows.length;
        await handleSaveInvoice();
        // Find the latest created
        await fetchInvoices();
        const updated = await api.get('/api/hr/invoices/');
        const latest = updated.data[0];
        if (latest) {
          await handleSendInvoice(latest.jd_id || 'direct', latest.id);
        }
      } else {
        // Existing invoice - update and send
        await handleSaveInvoice();
        await handleSendInvoice(selectedJob?.jd_id || 'direct', invoiceId);
        setEditingInvoiceId(null);
        setWasPreviouslySent(false);
      }
      await fetchInvoices();
    } catch (err) {
      console.error('Error sending invoice:', err);
      alert('Failed to send invoice. Please try again.');
    }
  };

  const handleCreateInvoice = (job) => {
    handleOpenInvoiceForm(job);
  };

  const handleEditInvoice = async (invoice) => {
    try {
      // Fetch full invoice details
      const response = await api.get(`/api/hr/invoices/${invoice.id}`);
      const invData = response.data;
      
      // Set editing state
      setEditingInvoiceId(invoice.id);
      setWasPreviouslySent(invoice.status === 'sent');
      
      // Find the job if it exists
      const job = invoice.jd_id ? jobs.find(j => j.id === invoice.jd_id) : null;
      setSelectedJob(job || { id: invoice.jd_id, jd_unique_id: invoice.jd_unique_id, client_name: invoice.client_name });
      
      // Populate form with invoice data
      setFormData({
        invoice_date: invData.invoice_date ? new Date(invData.invoice_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
        due_date: invData.due_date ? new Date(invData.due_date).toISOString().split('T')[0] : '',
        business_type_code: invData.business_type_code || businessTypes[0]?.code || '',
        invoice_type: invData.invoice_type || 'tax',
        calculate_tax: invData.total_tax > 0,
        company_name: invData.company_name || '',
        company_gstin: invData.company_gstin || '',
        company_pan: invData.company_pan || '',
        company_address: invData.company_address || '',
        company_phone: invData.company_phone || '',
        company_email: invData.company_email || '',
        company_website: invData.company_website || '',
        company_bank_name: invData.company_bank_name || '',
        company_bank_account: invData.company_bank_account || '',
        company_bank_ifsc: invData.company_bank_ifsc || '',
        company_bank_branch: invData.company_bank_branch || '',
        client_name: invData.client_name || '',
        client_email: invData.client_email || '',
        client_phone: invData.client_phone || '',
        client_billing_address: invData.client_billing_address || '',
        client_company_name: invData.client_company_name || '',
        client_gstin: invData.client_gstin || '',
        client_pan: invData.client_pan || '',
        place_of_supply: invData.place_of_supply || '',
        line_items: invData.line_items && invData.line_items.length > 0 
          ? invData.line_items.map(item => ({
              item_description: item.item_description || '',
              business_unique_id: item.business_unique_id || '',
              sac_code: item.sac_code || '998313',
              rate_per_item: item.rate_per_item || 0,
              quantity: item.quantity || 1,
              tax_rate: item.tax_rate || 18,
              taxable_value: item.taxable_value || 0,
              tax_amount: item.tax_amount || 0,
              amount: item.amount || 0
            }))
          : [{ item_description: '', business_unique_id: '', sac_code: '998313', rate_per_item: 0, quantity: 1, tax_rate: 18 }],
        notes: invData.notes || '',
        terms_and_conditions: invData.terms_and_conditions || ''
      });
      
      setShowInvoiceForm(true);
    } catch (err) {
      console.error('Error loading invoice for editing:', err);
      alert('Failed to load invoice. Please try again.');
    }
  };

  const handleSendInvoice = async (jobId, invoiceId) => {
    try {
      setSendingInvoice(jobId);
      const response = await api.post(`/api/hr/invoices/${invoiceId}/send`);
      
      // Update invoice status
      setInvoices(prev => ({
        ...prev,
        [jobId]: {
          ...prev[jobId],
          status: 'sent',
          sent_at: response.data.sent_at
        }
      }));
      
      alert('Invoice sent successfully via email!');
    } catch (err) {
      console.error('Error sending invoice:', err);
      alert('Failed to send invoice. Please try again.');
    } finally {
      setSendingInvoice(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  if (loading) {
    return (
      <div className="p-6">
        <Header 
          title="Invoice" 
          subtitle="Manage invoices for fulfilled job requirements"
        />
        <div className="mt-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Header 
          title="Invoice" 
          subtitle="Manage invoices for fulfilled job requirements"
        />
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={fetchInvoices}
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Header 
        title="Invoice" 
        subtitle="Manage invoices for fulfilled job requirements"
      />

      <div className="mt-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Fulfilled</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{jobs.length}</p>
              </div>
              <div className="p-3 rounded-lg bg-green-100">
                <BriefcaseIcon className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">With Invoice Date</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {jobs.filter(job => job.invoice_date).length}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-blue-100">
                <CalendarIcon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-sm p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Clients</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {new Set(jobs.map(job => job.client_name).filter(Boolean)).size}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-purple-100">
                <BuildingOfficeIcon className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </motion.div>
        </div>

        {/* Toolbar */}
        <div className="mb-4 flex items-center justify-end">
          <button
            onClick={handleOpenDirectInvoice}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            Create Invoice
          </button>
        </div>

        {/* Invoice Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white rounded-xl shadow-sm overflow-hidden"
        >
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Invoices
            </h3>
          </div>
          <div className="overflow-x-auto">
            {invoiceRows.length > 0 ? (
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Client Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Invoice Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {invoiceRows.map((inv) => (
                    <tr key={inv.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-mono text-gray-800">{inv.invoice_number || inv.jd_unique_id || '-'}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {inv.client_name || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatDate(inv.invoice_date)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{inv.source || '-'}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {inv.status === 'pending' || inv.id?.startsWith('jd-pending-') ? (
                            // For fulfilled JDs without invoices, show "Create Invoice"
                            <button
                              onClick={() => {
                                const job = jobs.find(j => j.id === inv.jd_id);
                                if (job) {
                                  handleOpenInvoiceForm(job);
                                } else {
                                  // Fallback: fetch the job or open direct invoice form
                                  api.get(`/api/hr/jds/${inv.jd_id}`)
                                    .then(res => {
                                      handleOpenInvoiceForm(res.data);
                                    })
                                    .catch(() => {
                                      handleOpenDirectInvoice();
                                    });
                                }
                              }}
                              className="px-3 py-2 text-sm font-medium rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors flex items-center space-x-1"
                            >
                              <DocumentArrowUpIcon className="h-4 w-4" />
                              <span>Create Invoice</span>
                            </button>
                          ) : inv.status === 'sent' || inv.status === 'draft' ? (
                            <>
                              <button
                                onClick={() => handleEditInvoice(inv)}
                                className="px-3 py-2 text-sm font-medium rounded-lg bg-yellow-100 text-yellow-700 hover:bg-yellow-200 transition-colors flex items-center space-x-1"
                              >
                                <DocumentArrowUpIcon className="h-4 w-4" />
                                <span>Edit Invoice</span>
                              </button>
                              {inv.status === 'draft' ? (
                                <button
                                  onClick={() => handleSendInvoice(inv.jd_id || 'direct', inv.id)}
                                  disabled={sendingInvoice === inv.id}
                                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1 ${
                                    sendingInvoice === inv.id
                                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                                  }`}
                                >
                                  <PaperAirplaneIcon className="h-4 w-4" />
                                  <span>{sendingInvoice === inv.id ? 'Sending...' : 'Send'}</span>
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleSendInvoice(inv.jd_id || 'direct', inv.id)}
                                  disabled={sendingInvoice === inv.id}
                                  className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors flex items-center space-x-1 ${
                                    sendingInvoice === inv.id
                                      ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                                  }`}
                                >
                                  <PaperAirplaneIcon className="h-4 w-4" />
                                  <span>{sendingInvoice === inv.id ? 'Resending...' : 'Resend'}</span>
                                </button>
                              )}
                            </>
                          ) : (
                            <>
                              <button
                                onClick={handleOpenDirectInvoice}
                                className="px-3 py-2 text-sm font-medium rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors flex items-center space-x-1"
                              >
                                <DocumentArrowUpIcon className="h-4 w-4" />
                                <span>Create Invoice</span>
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-12 text-center">
                <BriefcaseIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No invoices yet</h3>
                <p className="text-gray-500 mb-6">Click Create Invoice to add your first invoice.</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Invoice Form Modal */}
      {showInvoiceForm && selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white rounded-xl max-w-5xl w-full my-8 max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6 border-b border-gray-200 sticky top-0 bg-white z-10">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">Create Invoice</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {editingInvoiceId ? (
                      <>Editing Invoice {editingInvoiceId}</>
                    ) : selectedJob && selectedJob.id ? (
                      <>JD: {selectedJob.jd_unique_id || selectedJob.id} | Client: {selectedJob.client_name || 'N/A'}</>
                    ) : (
                      <>Direct Invoice</>
                    )}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setShowInvoiceForm(false);
                    setSelectedJob(null);
                    setEditingInvoiceId(null);
                    setWasPreviouslySent(false);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>

            <div className="p-6">
              <div className="space-y-6">
                {/* Invoice Dates */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Invoice Date *
                    </label>
                    <input
                      type="date"
                      value={formData.invoice_date}
                      onChange={(e) => handleFormChange('invoice_date', e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Due Date
                    </label>
                    <input
                      type="date"
                      value={formData.due_date}
                      onChange={(e) => handleFormChange('due_date', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Company Information */}
                <div className="border-t pt-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Your Company Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Company Name</label>
                      <input
                        type="text"
                        value={formData.company_name}
                        onChange={(e) => handleFormChange('company_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">GSTIN</label>
                      <input
                        type="text"
                        value={formData.company_gstin}
                        onChange={(e) => handleFormChange('company_gstin', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">PAN</label>
                      <input
                        type="text"
                        value={formData.company_pan}
                        onChange={(e) => handleFormChange('company_pan', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                      <input
                        type="text"
                        value={formData.company_phone}
                        onChange={(e) => handleFormChange('company_phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
                      <textarea
                        value={formData.company_address}
                        onChange={(e) => handleFormChange('company_address', e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                      <input
                        type="email"
                        value={formData.company_email}
                        onChange={(e) => handleFormChange('company_email', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Website</label>
                      <input
                        type="text"
                        value={formData.company_website}
                        onChange={(e) => handleFormChange('company_website', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Bank Name</label>
                      <input
                        type="text"
                        value={formData.company_bank_name}
                        onChange={(e) => handleFormChange('company_bank_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Account Number</label>
                      <input
                        type="text"
                        value={formData.company_bank_account}
                        onChange={(e) => handleFormChange('company_bank_account', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">IFSC Code</label>
                      <input
                        type="text"
                        value={formData.company_bank_ifsc}
                        onChange={(e) => handleFormChange('company_bank_ifsc', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Branch</label>
                      <input
                        type="text"
                        value={formData.company_bank_branch}
                        onChange={(e) => handleFormChange('company_bank_branch', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>

                {/* Client Information */}
                <div className="border-t pt-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">Client Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Client Name *</label>
                      <input
                        type="text"
                        value={formData.client_name}
                        onChange={(e) => handleFormChange('client_name', e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Client Email *</label>
                      <input
                        type="email"
                        value={formData.client_email}
                        onChange={(e) => handleFormChange('client_email', e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Client Phone</label>
                      <input
                        type="text"
                        value={formData.client_phone}
                        onChange={(e) => handleFormChange('client_phone', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Company Name</label>
                      <input
                        type="text"
                        value={formData.client_company_name}
                        onChange={(e) => handleFormChange('client_company_name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">GSTIN</label>
                      <input
                        type="text"
                        value={formData.client_gstin}
                        onChange={(e) => handleFormChange('client_gstin', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">PAN</label>
                      <input
                        type="text"
                        value={formData.client_pan}
                        onChange={(e) => handleFormChange('client_pan', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Billing Address</label>
                      <textarea
                        value={formData.client_billing_address}
                        onChange={(e) => handleFormChange('client_billing_address', e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Place of Supply</label>
                      <input
                        type="text"
                        value={formData.place_of_supply}
                        onChange={(e) => handleFormChange('place_of_supply', e.target.value)}
                        placeholder="e.g. 23-MADHYA PRADESH"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>

                {/* Business & Invoice Type */}
                <div className="border-t pt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Business Type</label>
                    <select
                      value={formData.business_type_code || ''}
                      onChange={(e) => handleFormChange('business_type_code', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="" disabled>Select business</option>
                      {businessTypes.map(bt => (
                        <option key={bt.code} value={bt.code}>{bt.name} ({bt.prefix})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Invoice Type</label>
                    <select
                      value={formData.invoice_type}
                      onChange={(e) => handleFormChange('invoice_type', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="tax">Tax Invoice</option>
                      <option value="proforma">Proforma Invoice</option>
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Tax Calculation</label>
                    <div className="flex items-center space-x-3 mt-2">
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.calculate_tax}
                          onChange={(e) => {
                            handleFormChange('calculate_tax', e.target.checked);
                            // Recalculate line items when tax toggle changes
                            const newLineItems = formData.line_items.map(item => {
                              const itemTotal = (item.rate_per_item || 0) * (item.quantity || 1);
                              const taxRate = item.tax_rate || 18;
                              const taxAmount = e.target.checked ? (itemTotal * (taxRate / 100)) : 0;
                              return {
                                ...item,
                                taxable_value: itemTotal,
                                tax_amount: taxAmount,
                                amount: itemTotal + taxAmount
                              };
                            });
                            setFormData(prev => ({ ...prev, line_items: newLineItems }));
                          }}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Calculate Tax</span>
                      </label>
                      <span className="text-xs text-gray-500">
                        {formData.calculate_tax ? 'Tax will be added to invoice' : 'Tax will not be added'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Line Items */}
                <div className="border-t pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="text-lg font-semibold text-gray-900">Invoice Items</h4>
                    <button
                      onClick={addLineItem}
                      className="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                    >
                      <PlusIcon className="h-4 w-4" />
                      <span>Add Item</span>
                    </button>
                  </div>
                  <div className="space-y-4">
                    {formData.line_items.map((item, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
                          <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Item Description</label>
                            <input
                              type="text"
                              value={item.item_description}
                              onChange={(e) => handleFormChange('item_description', e.target.value, index)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              placeholder="e.g. Hiring Services"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Business Unique ID</label>
                            <input
                              type="text"
                              value={item.business_unique_id || ''}
                              readOnly
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              placeholder="e.g. TP-SV-001"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Rate (₹)</label>
                            <input
                              type="number"
                              value={item.rate_per_item}
                              onChange={(e) => handleFormChange('rate_per_item', parseFloat(e.target.value) || 0, index)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Qty</label>
                            <input
                              type="number"
                              value={item.quantity}
                              onChange={(e) => handleFormChange('quantity', parseInt(e.target.value) || 1, index)}
                              min="1"
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Tax Rate (%)</label>
                            <input
                              type="number"
                              value={item.tax_rate}
                              onChange={(e) => handleFormChange('tax_rate', parseFloat(e.target.value) || 18, index)}
                              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                          </div>
                        </div>
                        <div className="mt-2 flex justify-between items-center">
                          <div className="text-sm text-gray-600">
                            Taxable: ₹{((item.rate_per_item || 0) * (item.quantity || 1)).toLocaleString('en-IN')} | 
                            Tax: ₹{formData.calculate_tax ? (((item.rate_per_item || 0) * (item.quantity || 1) * (item.tax_rate || 18) / 100).toLocaleString('en-IN')) : '₹0'} | 
                            Total: ₹{formData.calculate_tax ? (((item.rate_per_item || 0) * (item.quantity || 1) * (1 + (item.tax_rate || 18) / 100)).toLocaleString('en-IN')) : (((item.rate_per_item || 0) * (item.quantity || 1)).toLocaleString('en-IN'))}
                          </div>
                          {formData.line_items.length > 1 && (
                            <button
                              onClick={() => removeLineItem(index)}
                              className="text-red-600 hover:text-red-700 text-sm"
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Invoice Summary */}
                  {(() => {
                    const totals = calculateInvoiceTotals();
                    return (
                      <div className="mt-4 bg-gray-50 rounded-lg p-4">
                        <div className="flex justify-end">
                          <div className="w-64 space-y-2">
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">Subtotal:</span>
                              <span className="text-sm font-medium">₹{totals.subtotal.toLocaleString('en-IN')}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">CGST ({totals.cgstRate}%):</span>
                              <span className="text-sm font-medium">₹{totals.cgstAmount.toLocaleString('en-IN')}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600">SGST ({totals.sgstRate}%):</span>
                              <span className="text-sm font-medium">₹{totals.sgstAmount.toLocaleString('en-IN')}</span>
                            </div>
                            <div className="border-t pt-2 flex justify-between">
                              <span className="text-base font-semibold text-gray-900">Total Amount:</span>
                              <span className="text-base font-bold text-gray-900">₹{totals.totalAmount.toLocaleString('en-IN')}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* Notes & Terms */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t pt-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => handleFormChange('notes', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Terms & Conditions</label>
                    <textarea
                      value={formData.terms_and_conditions}
                      onChange={(e) => handleFormChange('terms_and_conditions', e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Form Footer */}
            <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowInvoiceForm(false);
                  setSelectedJob(null);
                  setEditingInvoiceId(null);
                  setWasPreviouslySent(false);
                }}
                className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveInvoice}
                className="px-4 py-2 text-white bg-yellow-600 rounded-lg hover:bg-yellow-700"
              >
                Save as Draft
              </button>
              <button
                onClick={handleSendInvoiceFromForm}
                className="px-4 py-2 text-white btn-gradient-primary rounded-lg"
              >
                {wasPreviouslySent ? 'Save & Resend Invoice' : 'Save & Send Invoice'}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Invoice;

