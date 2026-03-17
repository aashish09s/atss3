import React, { useEffect, useMemo, useState } from 'react';
import Header from '../../components/Header';
import api from '../../utils/api';

const PRESET_CATEGORIES = ['Rent','Salary','Electricity','Materials','Travel','Internet','Office','Other'];

const Expenses = () => {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState({ total_income:0, total_expenses:0, net_profit:0 });
  const [filters, setFilters] = useState({ category:'', start:'', end:'' });
  const [form, setForm] = useState({ category:'', title:'', amount:0, date: new Date().toISOString().split('T')[0], notes:'' });
  const [showPayment, setShowPayment] = useState(false);
  const [targetExpense, setTargetExpense] = useState(null);
  const [paymentForm, setPaymentForm] = useState({ amount: 0, payment_date: '', notes: '' });

  const fetchExpenses = async () => {
    try {
      const list = await api.get('/api/hr/expenses/', { params: { category: filters.category, start: filters.start || null, end: filters.end || null } });
      setItems(list.data || []);
      const sum = await api.get('/api/hr/expenses/summary', { params: { start: filters.start || null, end: filters.end || null } });
      setSummary(sum.data || { total_income:0, total_expenses:0, net_profit:0 });
    } catch (e) {
      console.error('Failed to load expenses', e);
    }
  };

  useEffect(()=>{ fetchExpenses(); }, []);

  const addExpense = async () => {
    if(!form.category && !form.title){ alert('Enter category or title'); return; }
    try {
      await api.post('/api/hr/expenses/', {
        category: form.category || (form.title || 'Other'),
        title: form.title,
        amount: parseFloat(form.amount) || 0,
        date: new Date(form.date).toISOString(),
        notes: form.notes
      });
      setForm({ category:'', title:'', amount:0, date: new Date().toISOString().split('T')[0], notes:'' });
      await fetchExpenses();
      alert('Expense added');
    } catch (e) {
      console.error('Failed to add expense', e);
      alert('Failed to add expense');
    }
  };

  const openPayment = (expense) => {
    const currentPaid = expense.paid_amount || 0;
    const remaining = expense.amount - currentPaid;
    setTargetExpense(expense);
    setPaymentForm({ 
      amount: remaining > 0 ? remaining : 0, 
      payment_date: new Date().toISOString().split('T')[0], 
      notes: '' 
    });
    setShowPayment(true);
  };

  const savePayment = async () => {
    try {
      const expenseId = targetExpense.id || targetExpense._id;
      if (!expenseId) {
        alert('Expense ID is missing. Please try again.');
        return;
      }
      
      const paymentAmount = parseFloat(paymentForm.amount) || 0;
      const currentPaid = targetExpense.paid_amount || 0;
      const newPaidAmount = currentPaid + paymentAmount;
      const totalAmount = targetExpense.amount;
      
      // Ensure paid amount doesn't exceed total
      const finalPaidAmount = newPaidAmount > totalAmount ? totalAmount : newPaidAmount;
      
      await api.patch(`/api/hr/expenses/${expenseId}/paid`, {
        paid_amount: finalPaidAmount
      });
      
      setShowPayment(false);
      setTargetExpense(null);
      await fetchExpenses();
      alert('Payment recorded successfully');
    } catch (e) {
      console.error('Failed to add payment', e);
      alert('Failed to add payment');
    }
  };

  // Simple category distribution visualization using widths
  const distribution = useMemo(()=>{
    const totals = {};
    items.forEach(i=>{ totals[i.category] = (totals[i.category]||0) + i.amount; });
    const total = Object.values(totals).reduce((a,b)=>a+b,0) || 1;
    return Object.entries(totals).map(([k,v])=>({ label:k, amount:v, pct: (v*100/total).toFixed(1) }));
  },[items]);

  return (
    <div className="p-6">
      <Header title="Expenses" subtitle="Track operational expenses and profit" />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="text-sm text-gray-600">Total Income</div>
          <div className="mt-2 text-2xl font-semibold text-green-600">₹{summary.total_income.toLocaleString('en-IN')}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="text-sm text-gray-600">Total Expenses</div>
          <div className="mt-2 text-2xl font-semibold text-red-600">₹{summary.total_expenses.toLocaleString('en-IN')}</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="text-sm text-gray-600">Net Profit / Loss</div>
          <div className={`mt-2 text-2xl font-semibold ${summary.net_profit>=0 ? 'text-green-700' : 'text-red-700'}`}>₹{summary.net_profit.toLocaleString('en-IN')}</div>
        </div>
      </div>

      {/* Add Expense */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6 grid grid-cols-1 md:grid-cols-6 gap-3">
        <select value={form.category} onChange={e=>setForm({...form, category:e.target.value})} className="px-3 py-2 border rounded-lg">
          <option value="">Select Category</option>
          {PRESET_CATEGORIES.map(c=> <option key={c} value={c}>{c}</option>)}
        </select>
        <input value={form.title} onChange={e=>setForm({...form, title:e.target.value})} className="px-3 py-2 border rounded-lg" placeholder="Or enter new category/title" />
        <input type="number" value={form.amount} onChange={e=>setForm({...form, amount:e.target.value})} className="px-3 py-2 border rounded-lg" placeholder="Amount" />
        <input type="date" value={form.date} onChange={e=>setForm({...form, date:e.target.value})} className="px-3 py-2 border rounded-lg" />
        <input value={form.notes} onChange={e=>setForm({...form, notes:e.target.value})} className="px-3 py-2 border rounded-lg" placeholder="Notes" />
        <button onClick={addExpense} className="px-4 py-2 rounded-lg bg-blue-600 text-white">Add Expense</button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-4 grid grid-cols-1 md:grid-cols-5 gap-3">
        <select value={filters.category} onChange={e=>setFilters({...filters, category:e.target.value})} className="px-3 py-2 border rounded-lg">
          <option value="">All Categories</option>
          {PRESET_CATEGORIES.map(c=> <option key={c} value={c}>{c}</option>)}
        </select>
        <input type="date" value={filters.start} onChange={e=>setFilters({...filters, start:e.target.value})} className="px-3 py-2 border rounded-lg" />
        <input type="date" value={filters.end} onChange={e=>setFilters({...filters, end:e.target.value})} className="px-3 py-2 border rounded-lg" />
        <button onClick={fetchExpenses} className="px-4 py-2 rounded-lg bg-blue-600 text-white">Filter</button>
        <button onClick={()=>{
          // simple CSV export
          const rows=[['Date','Category','Title','Amount','Notes'], ...items.map(i=>[new Date(i.date).toLocaleDateString('en-IN'),i.category,i.title||'',i.amount,i.notes||''])];
          const csv = rows.map(r=>r.join(',')).join('\n');
          const blob = new Blob([csv], {type:'text/csv'});
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href=url; a.download='expenses.csv'; a.click(); URL.revokeObjectURL(url);
        }} className="px-4 py-2 rounded-lg bg-gray-100">Export CSV</button>
      </div>

      {/* Distribution (simple bars) */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="text-sm font-semibold mb-2">Expense Distribution</div>
        <div className="space-y-2">
          {distribution.map(d=> (
            <div key={d.label} className="flex items-center space-x-3">
              <div className="w-40 text-sm text-gray-700">{d.label}</div>
              <div className="flex-1 bg-gray-100 h-3 rounded">
                <div className="h-3 bg-blue-500 rounded" style={{width: `${d.pct}%`}} />
              </div>
              <div className="w-24 text-right text-sm">₹{d.amount.toLocaleString('en-IN')}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Paid Amount</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Remaining</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {items.map(i => {
                const paid = i.paid_amount || 0;
                const remaining = i.amount - paid;
                const expenseId = i.id || i._id || '';
                return (
                  <tr key={expenseId} className="hover:bg-gray-50">
                    <td className="px-6 py-3 text-sm">{new Date(i.date).toLocaleDateString('en-IN')}</td>
                    <td className="px-6 py-3 text-sm">{i.category}</td>
                    <td className="px-6 py-3 text-sm">{i.title || '-'}</td>
                    <td className="px-6 py-3 text-right text-sm">₹{i.amount.toLocaleString('en-IN')}</td>
                    <td className="px-6 py-3 text-right text-sm text-green-700">₹{paid.toLocaleString('en-IN')}</td>
                    <td className={`px-6 py-3 text-right text-sm ${remaining > 0 ? 'text-red-700' : 'text-green-700'}`}>
                      ₹{remaining.toLocaleString('en-IN')}
                    </td>
                    <td className="px-6 py-3 text-sm">{i.notes || '-'}</td>
                    <td className="px-6 py-3 text-sm">
                      <button
                        onClick={() => openPayment({ ...i, id: expenseId })}
                        className="px-3 py-1 rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200"
                      >
                        Add Payment
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Payment Modal */}
      {showPayment && targetExpense && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl w-full max-w-lg p-6">
            <div className="text-lg font-semibold mb-4">Add Payment - {targetExpense.category} - {targetExpense.title || 'Expense'}</div>
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm text-gray-600">Total Amount: <span className="font-medium">₹{targetExpense.amount.toLocaleString('en-IN')}</span></div>
              <div className="text-sm text-gray-600 mt-1">Already Paid: <span className="font-medium text-green-700">₹{(targetExpense.paid_amount || 0).toLocaleString('en-IN')}</span></div>
              <div className="text-sm text-gray-600 mt-1">Remaining: <span className="font-medium text-red-700">₹{(targetExpense.amount - (targetExpense.paid_amount || 0)).toLocaleString('en-IN')}</span></div>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Payment Amount</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border rounded-lg"
                  value={paymentForm.amount}
                  onChange={(e) => setPaymentForm({...paymentForm, amount: e.target.value})}
                  placeholder="Amount"
                  max={targetExpense.amount - (targetExpense.paid_amount || 0)}
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Payment Date</label>
                <input
                  type="date"
                  className="w-full px-3 py-2 border rounded-lg"
                  value={paymentForm.payment_date}
                  onChange={(e) => setPaymentForm({...paymentForm, payment_date: e.target.value})}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes</label>
                <textarea
                  className="w-full px-3 py-2 border rounded-lg"
                  rows={3}
                  value={paymentForm.notes}
                  onChange={(e) => setPaymentForm({...paymentForm, notes: e.target.value})}
                  placeholder="Payment notes or transaction reference"
                />
              </div>
            </div>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowPayment(false);
                  setTargetExpense(null);
                }}
                className="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={savePayment}
                className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
              >
                Save Payment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Expenses;


