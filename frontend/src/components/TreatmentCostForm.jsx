import React, { useState, useEffect } from 'react';
import {
  estimateTreatmentCost,
  calculateCoverage,
  getTreatmentOptions,
  getActivePolicyStatus,
} from '../services/api';

const DEFAULT_TREATMENTS = [
  'Knee Replacement',
  'Cataract Surgery',
  'Appendectomy',
  'CABG',
  'Angioplasty',
  'Hip Replacement',
  'Hernia Repair',
  'C-Section',
  'Gallbladder Surgery',
  'Kidney Stone Surgery',
];

const DEFAULT_CITIES = ['Pune', 'Mumbai', 'Delhi'];
const DEFAULT_HOSPITAL_TYPES = ['Private', 'Government'];

const TreatmentCostForm = () => {
  const [treatment, setTreatment] = useState('Knee Replacement');
  const [city, setCity] = useState('Pune');
  const [hospitalType, setHospitalType] = useState('Private');

  // Policy factors (initialized with demo values or extracted from active policy)
  const [sumInsured, setSumInsured] = useState(500000);
  const [deductible, setDeductible] = useState(5000);
  const [copayPercent, setCopayPercent] = useState(10);
  const [treatmentSubLimit, setTreatmentSubLimit] = useState(150000);
  const [showConfig, setShowConfig] = useState(true);

  const [options, setOptions] = useState({
    treatments: DEFAULT_TREATMENTS,
    cities: DEFAULT_CITIES,
    hospital_types: DEFAULT_HOSPITAL_TYPES,
  });

  const [loading, setLoading] = useState(false);
  const [costResult, setCostResult] = useState(null);
  const [coverageResult, setCoverageResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const opts = await getTreatmentOptions();
      if (opts && opts.treatments?.length) {
        setOptions({
          treatments: opts.treatments,
          cities: opts.cities?.length ? opts.cities : DEFAULT_CITIES,
          hospital_types: opts.hospital_types?.length ? opts.hospital_types : DEFAULT_HOSPITAL_TYPES,
        });
      }

      // Check active policy for auto-extracted parameters
      const status = await getActivePolicyStatus();
      if (status?.is_uploaded && status?.policy_config) {
        const cfg = status.policy_config;
        if (cfg.sum_insured) setSumInsured(cfg.sum_insured);
        if (cfg.deductible) setDeductible(cfg.deductible);
        if (cfg.copay_percent) setCopayPercent(cfg.copay_percent);
        if (cfg.sub_limits && cfg.sub_limits['Cataract Surgery'] && treatment === 'Cataract Surgery') {
          setTreatmentSubLimit(cfg.sub_limits['Cataract Surgery']);
        }
      }
    } catch (err) {
      console.warn('Initial data load warning:', err);
    }
  };

  const handleEstimateAndCalculate = async (e) => {
    if (e) e.preventDefault();
    if (!treatment) return;

    setLoading(true);
    setError(null);
    setCostResult(null);
    setCoverageResult(null);

    try {
      // 1. Get synthetic treatment cost
      const costData = await estimateTreatmentCost(treatment, city, hospitalType);
      setCostResult(costData);

      // 2. Perform deterministic coverage calculation in Python
      const coverageData = await calculateCoverage({
        treatment,
        city,
        hospital_type: hospitalType,
        estimated_treatment_cost: costData.typical_cost,
        sum_insured: sumInsured ? Number(sumInsured) : null,
        deductible: deductible !== '' ? Number(deductible) : null,
        copay_percent: copayPercent !== '' ? Number(copayPercent) : null,
        treatment_sub_limit: treatmentSubLimit ? Number(treatmentSubLimit) : null,
      });

      if (coverageData.is_available === false) {
        setError(coverageData.error || 'Coverage estimate unavailable because the policy does not provide enough information.');
      } else {
        setCoverageResult(coverageData);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 404 || detail?.includes('No matching')) {
        setError('No matching treatment-cost data available.');
      } else {
        setError(detail || 'Coverage estimate unavailable because the policy does not provide enough information.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-xs border border-slate-200 p-6 space-y-6">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
          Step 3: Treatment Cost & Deterministic Coverage Calculator
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Estimate synthetic treatment cost and calculate out-of-pocket coverage deterministically.
        </p>
      </div>

      <form onSubmit={handleEstimateAndCalculate} className="space-y-4">
        {/* Treatment, City, Hospital Type */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Treatment:
            </label>
            <select
              value={treatment}
              onChange={(e) => {
                const val = e.target.value;
                setTreatment(val);
                if (val === 'Cataract Surgery') {
                  setTreatmentSubLimit(40000);
                } else if (val === 'Knee Replacement') {
                  setTreatmentSubLimit(150000);
                }
              }}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-2xs font-medium"
            >
              {options.treatments.map((t, idx) => (
                <option key={idx} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              City:
            </label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-2xs font-medium"
            >
              {options.cities.map((c, idx) => (
                <option key={idx} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600">
              Hospital Type:
            </label>
            <select
              value={hospitalType}
              onChange={(e) => setHospitalType(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-2xs font-medium"
            >
              {options.hospital_types.map((h, idx) => (
                <option key={idx} value={h}>
                  {h}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Policy Factors Configuration Box */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <span>⚙️</span>
              <span>Policy Rule Factors (Extracted / Configurable):</span>
            </span>
            <button
              type="button"
              onClick={() => setShowConfig(!showConfig)}
              className="text-xs text-blue-600 hover:text-blue-800 font-semibold"
            >
              {showConfig ? 'Hide Factors' : 'Edit Factors'}
            </button>
          </div>

          {showConfig && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                  1. Sum Insured (₹)
                </label>
                <input
                  type="number"
                  value={sumInsured}
                  onChange={(e) => setSumInsured(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono text-slate-800"
                  placeholder="500000"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                  2. Sub-Limit (₹)
                </label>
                <input
                  type="number"
                  value={treatmentSubLimit}
                  onChange={(e) => setTreatmentSubLimit(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono text-slate-800"
                  placeholder="150000"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                  3. Deductible (₹)
                </label>
                <input
                  type="number"
                  value={deductible}
                  onChange={(e) => setDeductible(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono text-slate-800"
                  placeholder="5000"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                  4. Co-pay (%)
                </label>
                <input
                  type="number"
                  value={copayPercent}
                  onChange={(e) => setCopayPercent(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono text-slate-800"
                  placeholder="10"
                />
              </div>
            </div>
          )}
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-all shadow-xs disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Computing Deterministic Coverage...
              </>
            ) : (
              <span>[ Estimate Cost & Coverage ]</span>
            )}
          </button>
        </div>
      </form>

      {/* Error / Incomplete Policy Rules Notice */}
      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 font-medium space-y-1">
          <div className="font-bold flex items-center gap-1.5">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
          <p className="text-xs text-amber-700">
            Ensure the policy contains sum insured, deductible, and co-payment terms before estimating coverage.
          </p>
        </div>
      )}

      {/* Results Display */}
      {costResult && coverageResult && (
        <div className="space-y-5">
          {/* Synthetic Cost Card */}
          <div className="p-5 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-b border-slate-200 pb-2">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  {costResult.city} • {costResult.hospital_type} Hospital
                </span>
                <h3 className="text-base font-extrabold text-slate-900">{costResult.treatment}</h3>
              </div>
              <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-semibold self-start sm:self-auto">
                Synthetic Benchmark
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3 bg-white rounded-lg border border-slate-200">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Estimated Treatment Cost
                </span>
                <span className="text-xl font-extrabold text-blue-600 block mt-0.5">
                  {costResult.formatted_typical_cost}
                </span>
              </div>

              <div className="p-3 bg-white rounded-lg border border-slate-200">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Cost Range
                </span>
                <span className="text-lg font-bold text-slate-800 block mt-0.5">
                  {costResult.formatted_cost_range}
                </span>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 italic">
              ℹ️ "{costResult.disclaimer}"
            </p>
          </div>

          {/* Deterministic Coverage Card */}
          <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Deterministic Coverage Result
                </span>
                <h3 className="text-base font-extrabold text-slate-900">
                  Policy-to-Patient Coverage Calculation
                </h3>
              </div>
              <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-md">
                Deterministic Arithmetic
              </span>
            </div>

            {/* Big Highlights: Covered vs Out-of-Pocket */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-xl space-y-1 text-center sm:text-left">
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">
                  Potentially Covered Amount
                </span>
                <span className="text-3xl font-extrabold text-emerald-700 block">
                  {coverageResult.formatted_values.potentially_covered}
                </span>
                <span className="text-[11px] text-emerald-700 block">
                  Subject to claim terms and sum insured limits.
                </span>
              </div>

              <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-xl space-y-1 text-center sm:text-left">
                <span className="text-xs font-bold text-amber-800 uppercase tracking-wider">
                  Estimated Out-of-Pocket
                </span>
                <span className="text-3xl font-extrabold text-amber-700 block">
                  {coverageResult.formatted_values.estimated_out_of_pocket}
                </span>
                <span className="text-[11px] text-amber-700 block">
                  Deductible + Co-payment + Amount exceeding sub-limit.
                </span>
              </div>
            </div>

            {/* Arithmetic Breakdown Sequence */}
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-1">
                Calculation Sequence (Python Deterministic Arithmetic):
              </span>
              <div className="space-y-1.5 text-xs text-slate-700 font-mono">
                <div className="flex justify-between py-1 border-b border-slate-200">
                  <span>Estimated Treatment Cost:</span>
                  <span className="font-semibold text-slate-900">
                    {coverageResult.formatted_values.estimated_treatment_cost}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200">
                  <span>Treatment Sub-Limit Applied (Eligible Base):</span>
                  <span className="font-semibold text-slate-900">
                    {coverageResult.formatted_values.eligible_amount}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200">
                  <span>Deductible Applied:</span>
                  <span className="font-semibold text-red-600">
                    - {coverageResult.formatted_values.deductible}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200">
                  <span>Co-payment Applied:</span>
                  <span className="font-semibold text-red-600">
                    - {coverageResult.formatted_values.copay}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-200 bg-emerald-50/60 px-2 rounded font-bold text-emerald-800">
                  <span>= Potentially Covered Amount:</span>
                  <span>{coverageResult.formatted_values.potentially_covered}</span>
                </div>
                <div className="flex justify-between py-1 bg-amber-50/60 px-2 rounded font-bold text-amber-900">
                  <span>= Estimated Out-of-Pocket:</span>
                  <span>{coverageResult.formatted_values.estimated_out_of_pocket}</span>
                </div>
              </div>
            </div>

            {/* Policy Rules Applied & Citations */}
            {coverageResult.policy_rules_applied && coverageResult.policy_rules_applied.length > 0 && (
              <div className="space-y-2 pt-1">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                  Policy Rules Used & Citations:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {coverageResult.policy_rules_applied.map((rule, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-blue-50/60 border border-blue-200/70 rounded-lg text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-blue-900">{rule.rule}</span>
                        <span className="px-1.5 py-0.5 bg-blue-200/80 text-blue-800 font-semibold rounded text-[10px]">
                          Page {rule.page}
                        </span>
                      </div>
                      <div className="font-mono text-slate-800 font-semibold">{rule.value}</div>
                      <div className="text-[11px] text-slate-600">{rule.note}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mandatory Coverage Disclaimer */}
            <div className="pt-3 border-t border-slate-200 text-xs text-slate-600 italic font-medium">
              ⚖️ "{coverageResult.disclaimer}"
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TreatmentCostForm;
