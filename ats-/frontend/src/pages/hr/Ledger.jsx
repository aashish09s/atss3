import React, { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import api from '../../utils/api';

const Ledger = () => {
  const [rows, setRows] = useState([]);
  const [summary, setSummary] = useState({ total_invoiced: 0, total_received: 0, total_tds: 0, total_outstanding: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ invoice_number: '', client_name: '', payment_status: '' });
  const [showPayment, setShowPayment] = useState(false);
  const [targetInvoice, setTargetInvoice] = useState(null);
  const [paymentForm, setPaymentForm] = useState({ amount: 0, payment_date: '', transaction_ref: '', remarks: '' });
  const [editingTds, setEditingTds] = useState(null);
  const [tdsValue, setTdsValue] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      // Only include non-empty filters in the API call
      const params = {};
      if (filters.invoice_number && filters.invoice_number.trim()) {
        params.invoice_number = filters.invoice_number.trim();
      }
      if (filters.client_name && filters.client_name.trim()) {
        params.client_name = filters.client_name.trim();
      }
      if (filters.payment_status && filters.payment_status.trim()) {
        params.payment_status = filters.payment_status.trim();
      }
      
      const list = await api.get('/api/hr/ledger/', { params });
      setRows(list.data || []);
      const sum = await api.get('/api/hr/ledger/summary');
      setSummary(sum.data || { total_invoiced: 0, total_received: 0, total_tds: 0, total_outstanding: 0 });
    } catch (e) {
      console.error('Failed to load ledger', e);
      alert('Failed to load ledger data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    fetchData(); 
    // Refresh every 30 seconds to catch newly sent invoices
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const openPayment = (inv) => {
    setTargetInvoice(inv);
    setPaymentForm({ amount: inv.outstanding || 0, payment_date: new Date().toISOString().split('T')[0], transaction_ref: '', remarks: '' });
    setShowPayment(true);
  };

  const savePayment = async () => {
    try {
      await api.post(`/api/hr/ledger/${targetInvoice.id}/payments`, {
        amount: parseFloat(paymentForm.amount) || 0,
        payment_date: new Date(paymentForm.payment_date).toISOString(),
        transaction_ref: paymentForm.transaction_ref,
        remarks: paymentForm.remarks
      });
      setShowPayment(false);
      setTargetInvoice(null);
      await fetchData();
      alert('Payment recorded');
    } catch (e) {
      console.error('Failed to add payment', e);
      alert('Failed to add payment');
    }
  };

  const startEditTds = (row) => {
    setEditingTds(row.id);
    setTdsValue(row.tds_amount || '0');
  };

  const saveTds = async (invoiceId) => {
    try {
      const tdsAmount = parseFloat(tdsValue) || 0;
      await api.patch(`/api/hr/invoices/${invoiceId}/tds`, {
        tds_amount: tdsAmount
      });
      setEditingTds(null);
      setTdsValue('');
      await fetchData();
      alert('TDS updated successfully');
    } catch (e) {
      console.error('Failed to update TDS', e);
      alert('Failed to update TDS');
    }
  };

  const cancelEditTds = () => {
    setEditingTds(null);
    setTdsValue('');
  };

  const calculateDaysPassed = (invoiceDate) => {
    if (!invoiceDate) return '-';
    const invoice = new Date(invoiceDate);
    const today = new Date();
    // Reset time to midnight for accurate day calculation
    invoice.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    const diffTime = today - invoice;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  return (
    <div className="p-6">
      <Header title="Ledger" subtitle="Track payments and outstanding balances" />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="text-sm text-gray-600">Total Invoiced</div>
          <div className="mt-2 text-2xl font-semibold">₹{summary.total_invoiced.toLocaleString('en-IN')}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="text-sm text-gray-600">Total Received</div>
          <div className="mt-2 text-2xl font-semibold text-green-600">₹{summary.total_received.toLocaleString('en-IN')}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="text-sm text-gray-600">Total Outstanding</div>
          <div className="mt-2 text-2xl font-semibold text-red-600">₹{summary.total_outstanding.toLocaleString('en-IN')}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-4 grid grid-cols-1 md:grid-cols-5 gap-4">
        <input className="px-3 py-2 border rounded-lg" placeholder="Invoice ID" value={filters.invoice_number} onChange={e=>setFilters({...filters, invoice_number:e.target.value})} />
        <input className="px-3 py-2 border rounded-lg" placeholder="Client Name" value={filters.client_name} onChange={e=>setFilters({...filters, client_name:e.target.value})} />
        <select className="px-3 py-2 border rounded-lg" value={filters.payment_status} onChange={e=>setFilters({...filters, payment_status:e.target.value})}>
          <option value="">All Status</option>
          <option value="paid">Fully Paid</option>
          <option value="partial">Partially Paid</option>
          <option value="pending">Pending</option>
        </select>
        <button onClick={fetchData} className="px-4 py-2 rounded-lg bg-blue-600 text-white">Apply</button>
        <button 
          onClick={fetchData} 
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-1" 
          title="Refresh to see newly sent invoices"
        >
          <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Client</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice Date</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Days Passed</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Received</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Outstanding</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">TDS</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {rows.map(row => (
                <tr key={row.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 font-mono text-sm">{row.invoice_number}</td>
                  <td className="px-6 py-3 text-sm">{row.client_name}</td>
                  <td className="px-6 py-3 text-sm">{new Date(row.invoice_date).toLocaleDateString('en-IN')}</td>
                  <td className="px-6 py-3 text-center text-sm">
                    <span className={`px-2 py-1 rounded ${
                      calculateDaysPassed(row.invoice_date) >= 90 
                        ? 'bg-red-100 text-red-700' 
                        : calculateDaysPassed(row.invoice_date) >= 30 
                        ? 'bg-yellow-100 text-yellow-700' 
                        : 'bg-green-100 text-green-700'
                    }`}>
                      {calculateDaysPassed(row.invoice_date)} {calculateDaysPassed(row.invoice_date) === 1 ? 'day' : 'days'}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right text-sm">₹{row.total_amount.toLocaleString('en-IN')}</td>
                  <td className="px-6 py-3 text-right text-sm text-green-700">₹{row.received_amount.toLocaleString('en-IN')}</td>
                  <td className="px-6 py-3 text-right text-sm text-red-700">₹{row.outstanding.toLocaleString('en-IN')}</td>
                  <td className="px-6 py-3 text-sm">
                    {editingTds === row.id ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="number"
                          value={tdsValue}
                          onChange={(e) => setTdsValue(e.target.value)}
                          className="w-24 px-2 py-1 border rounded text-right"
                          placeholder="0"
                          autoFocus
                        />
                        <button
                          onClick={() => saveTds(row.id)}
                          className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                        >
                          ✓
                        </button>
                        <button
                          onClick={cancelEditTds}
                          className="px-2 py-1 text-xs bg-gray-600 text-white rounded hover:bg-gray-700"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-end space-x-2">
                        <span className="text-sm text-gray-700">₹{(row.tds_amount || 0).toLocaleString('en-IN')}</span>
                        <button
                          onClick={() => startEditTds(row)}
                          className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200"
                          title="Edit TDS"
                        >
                          Edit
                        </button>
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-3 text-sm">
                    <button onClick={()=>openPayment(row)} className="px-3 py-1 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200">Add Payment</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Payment Modal */}
      {showPayment && targetInvoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl w-full max-w-lg p-6">
            <div className="text-lg font-semibold mb-4">Add Payment - {targetInvoice.invoice_number}</div>
            <div className="grid grid-cols-1 gap-4">
              <input type="number" className="px-3 py-2 border rounded-lg" value={paymentForm.amount} onChange={e=>setPaymentForm({...paymentForm, amount: e.target.value})} placeholder="Amount" />
              <input type="date" className="px-3 py-2 border rounded-lg" value={paymentForm.payment_date} onChange={e=>setPaymentForm({...paymentForm, payment_date: e.target.value})} />
              <input type="text" className="px-3 py-2 border rounded-lg" value={paymentForm.transaction_ref} onChange={e=>setPaymentForm({...paymentForm, transaction_ref: e.target.value})} placeholder="Transaction Ref" />
              <textarea className="px-3 py-2 border rounded-lg" rows={3} value={paymentForm.remarks} onChange={e=>setPaymentForm({...paymentForm, remarks: e.target.value})} placeholder="Remarks" />
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button onClick={()=>{setShowPayment(false); setTargetInvoice(null);}} className="px-4 py-2 rounded-lg bg-gray-100">Cancel</button>
              <button onClick={savePayment} className="px-4 py-2 rounded-lg bg-blue-600 text-white">Save Payment</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Ledger;


