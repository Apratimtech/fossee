const API_BASE = import.meta.env.VITE_API_URL || '/api';

function b64(s) {
  return btoa(unescape(encodeURIComponent(s)));
}

function getAuthHeader(credentials) {
  if (!credentials?.username || !credentials?.password) return {};
  const encoded = b64(`${credentials.username}:${credentials.password}`);
  return { Authorization: `Basic ${encoded}` };
}

export async function api(method, path, { body, credentials, formData } = {}) {
  const headers = {};
  Object.assign(headers, getAuthHeader(credentials));
  if (!formData) headers['Content-Type'] = 'application/json';

  const opts = {
    method,
    headers,
    credentials: 'omit',
  };
  if (body && !formData) opts.body = JSON.stringify(body);
  if (formData) {
    delete headers['Content-Type'];
    opts.body = formData;
    Object.assign(opts.headers, getAuthHeader(credentials));
  }

  const res = await fetch(`${API_BASE}${path}`, opts);
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  if (!res.ok) {
    const err = new Error(data?.error || data?.detail || res.statusText || `HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export async function uploadFile(file, credentials) {
  const form = new FormData();
  form.append('file', file);
  return api('POST', '/upload/', { formData: form, credentials });
}

export async function getSummary(uploadId, credentials) {
  return api('GET', `/summary/${uploadId}/`, { credentials });
}

export async function getData(uploadId, credentials) {
  return api('GET', `/data/${uploadId}/`, { credentials });
}

export async function getHistory(credentials) {
  return api('GET', '/history/', { credentials });
}

export async function downloadReport(uploadId, filename, credentials) {
  const headers = getAuthHeader(credentials);
  const res = await fetch(`${API_BASE}/report/${uploadId}/pdf/`, {
    method: 'GET',
    headers,
    credentials: 'omit',
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename ? `report_${filename}` : `report_${uploadId}.pdf`;
  a.click();
  URL.revokeObjectURL(a.href);
}
