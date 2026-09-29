import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// ── Policy Engine API ─────────────────────────────────────────────────────────

export const uploadPolicyPdf = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/policy/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const askPolicy = async (question, policyId = null) => {
  const payload = { question };
  if (policyId) {
    payload.policy_id = policyId;
  }
  const response = await api.post('/policy/ask', payload);
  return response.data;
};

export const getActivePolicyStatus = async () => {
  const response = await api.get('/policy/active');
  return response.data;
};

// ── Treatment Cost & Deterministic Coverage API ───────────────────────────────

export const estimateTreatmentCost = async (treatment, city = 'Pune', hospitalType = 'Private') => {
  const response = await api.post('/treatment/estimate', {
    treatment,
    city,
    hospital_type: hospitalType,
  });
  return response.data;
};

export const calculateCoverage = async (params) => {
  const response = await api.post('/treatment/coverage', params);
  return response.data;
};

export const getTreatmentOptions = async () => {
  const response = await api.get('/treatment/options');
  return response.data;
};

// ── Backward-compatible helpers ───────────────────────────────────────────────

export const uploadPolicy = uploadPolicyPdf;
export const askQuestion = async (policyId, question) => askPolicy(question, policyId);
export const listPolicies = async () => (await api.get('/policies')).data;
export const getPolicy = async (policyId) => (await api.get(`/policies/${policyId}`)).data;
export const getTreatmentCatalog = async () => (await api.get('/treatment/catalog')).data;
