import React, { useState, useEffect } from 'react';
import { uploadPolicy, listPolicies, getPolicy } from '../services/api';

const PolicyUpload = ({ activePolicy, setActivePolicy }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [policies, setPolicies] = useState([]);
  const [loadingPolicies, setLoadingPolicies] = useState(false);

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    setLoadingPolicies(true);
    try {
      const data = await listPolicies();
      setPolicies(data);
    } catch (err) {
      console.error('Error fetching policies', err);
    } finally {
      setLoadingPolicies(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await uploadPolicy(file);
      await fetchPolicies();
      setFile(null);
      // Backend returns { policy_id, filename, message }
      if (result && result.policy_id) {
         const fullPolicy = await getPolicy(result.policy_id);
         setActivePolicy(fullPolicy);
      }
    } catch (err) {
      setError('Failed to upload policy. Make sure backend is running.');
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleSelectPolicy = async (policyId) => {
    try {
      const fullPolicy = await getPolicy(policyId);
      setActivePolicy(fullPolicy);
    } catch (err) {
      console.error('Failed to select policy', err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 mb-4">📤 Upload New Policy</h2>
        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <input
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-indigo-50 file:text-indigo-700
              hover:file:bg-indigo-100 transition-colors cursor-pointer"
          />
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="w-full sm:w-auto px-6 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading & Indexing...' : 'Upload'}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 mb-4">📚 Available Policies</h2>
        
        {loadingPolicies ? (
          <p className="text-gray-500">Loading policies...</p>
        ) : policies.length === 0 ? (
          <p className="text-gray-500">No policies available. Upload one to get started.</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {policies.map((p) => {
              const isActive = activePolicy?.policy_id === p.policy_id;
              return (
                <div
                  key={p.policy_id}
                  className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                    isActive
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-indigo-300'
                  }`}
                  onClick={() => handleSelectPolicy(p.policy_id)}
                >
                  <h3 className="font-semibold text-gray-800 truncate" title={p.filename}>
                    {p.filename || `Policy ${p.policy_id.substring(0, 8)}...`}
                  </h3>
                  <div className="mt-2 text-sm text-gray-600">
                    <p>Uploaded: {new Date(p.uploaded_at).toLocaleDateString()}</p>
                  </div>
                  <div className="mt-4">
                    <button
                      className={`text-sm font-medium w-full py-1.5 rounded ${
                        isActive
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectPolicy(p.policy_id);
                      }}
                    >
                      {isActive ? '✅ Selected' : 'Select Policy'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {activePolicy && (
        <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-100">
          <h2 className="text-lg font-bold text-indigo-900 mb-2">✅ Active Policy Info</h2>
          <ul className="text-sm text-indigo-800 space-y-1">
            <li><strong>ID:</strong> {activePolicy.policy_id}</li>
            <li><strong>Filename:</strong> {activePolicy.filename}</li>
            <li><strong>Pages:</strong> {activePolicy.page_count}</li>
            <li><strong>Chunks Indexed:</strong> {activePolicy.chunks_count}</li>
            <li><strong>Indexed:</strong> {activePolicy.is_indexed ? '✅ Yes' : '❌ No'}</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default PolicyUpload;
