import React, { useState, useEffect } from 'react';
import { getTreatmentCatalog, estimateCost } from '../services/api';

const CostEstimator = ({ activePolicy }) => {
  const [catalog, setCatalog] = useState([]);
  const [selectedTreatment, setSelectedTreatment] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const data = await getTreatmentCatalog();
        setCatalog(data);
      } catch (err) {
        console.error('Failed to fetch treatment catalog', err);
      }
    };
    fetchCatalog();
  }, []);

  if (!activePolicy) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-xl text-center">
        <p className="text-yellow-700 font-medium">⚠️ Please upload or select a policy first.</p>
      </div>
    );
  }

  const handleEstimate = async () => {
    if (!selectedTreatment) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await estimateCost(activePolicy.policy_id, selectedTreatment);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError('Failed to calculate estimate. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return '-';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 mb-4">💰 Treatment Cost Estimator</h2>
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-grow">
            <select
              value={selectedTreatment}
              onChange={(e) => setSelectedTreatment(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-gray-700"
            >
              <option value="">-- Select a Treatment --</option>
              {catalog.map((item, idx) => (
                <option key={idx} value={item.name}>
                  {item.name} {item.cpt_code ? `(CPT: ${item.cpt_code})` : ''} - Avg: {formatCurrency(item.average_cost)}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleEstimate}
            disabled={!selectedTreatment || loading}
            className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors whitespace-nowrap"
          >
            {loading ? 'Calculating...' : 'Estimate Cost'}
          </button>
        </div>
        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      </div>

      {result && (
        <div className="bg-white p-8 rounded-xl shadow-lg border border-gray-100">
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold text-gray-800">{result.treatment_name}</h3>
            <p className="text-gray-500 mt-1">Cost Estimate based on {activePolicy.filename}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gray-50 p-6 rounded-xl border border-gray-100 text-center">
              <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Total Average Cost</p>
              <p className="text-3xl font-bold text-gray-800">{formatCurrency(result.estimated_cost)}</p>
            </div>

            <div className="bg-green-50 p-6 rounded-xl border border-green-100 text-center shadow-inner">
              <p className="text-sm text-green-600 font-medium uppercase tracking-wider mb-1">Insurance Covers</p>
              <p className="text-3xl font-bold text-green-700">{formatCurrency(result.coverage?.covered_amount)}</p>
            </div>

            <div className="bg-orange-50 p-6 rounded-xl border border-orange-100 text-center shadow-inner">
              <p className="text-sm text-orange-600 font-medium uppercase tracking-wider mb-1">You Pay (Out of Pocket)</p>
              <p className="text-3xl font-bold text-orange-600">{formatCurrency(result.coverage?.out_of_pocket)}</p>
            </div>
          </div>

          <div className="bg-blue-50/50 p-6 rounded-xl border border-blue-100">
            <h4 className="font-semibold text-blue-900 mb-4 flex items-center gap-2">
              📊 Breakdown & Details
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-3 gap-x-8 text-sm">
              <div className="flex justify-between border-b border-blue-100 pb-2">
                <span className="text-gray-600">Deductible Applied:</span>
                <span className="font-medium text-gray-900">{formatCurrency(result.coverage?.deductible_applied)}</span>
              </div>
              <div className="flex justify-between border-b border-blue-100 pb-2">
                <span className="text-gray-600">Copay / Co-insurance:</span>
                <span className="font-medium text-gray-900">{formatCurrency(result.coverage?.copay)}</span>
              </div>
            </div>

            {result.coverage?.notes && (
              <div className="mt-4 pt-4 border-t border-blue-100">
                <p className="text-sm text-blue-800 bg-blue-100/50 p-3 rounded-lg leading-relaxed">
                  <strong>💡 Note:</strong> {result.coverage.notes}
                </p>
              </div>
            )}

            {result.disclaimer && (
              <div className="mt-3">
                <p className="text-xs text-gray-400 italic">{result.disclaimer}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CostEstimator;
