import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function getApiErrorMessage(error, fallbackMessage = 'Something went wrong') {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }

  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  if (error.code === 'ERR_NETWORK') {
    return `Cannot connect to API at ${API_BASE_URL}. Check that the backend is running and VITE_API_URL is correct.`;
  }

  return fallbackMessage;
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || '';
    const isAuthRequest =
      requestUrl.includes('/auth/login') ||
      requestUrl.includes('/auth/refresh') ||
      requestUrl.includes('/auth/logout');

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthRequest
    ) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);

          originalRequest.headers = {
            ...originalRequest.headers,
            Authorization: `Bearer ${data.access_token}`,
          };

          return apiClient(originalRequest);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export const authApi = {
  login: (username, password) =>
    apiClient.post('/auth/login', {
      username: username.trim(),
      password,
    }),
  me: () => apiClient.get('/auth/me'),
  refresh: (refreshToken) =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: (refreshToken) =>
    apiClient.post('/auth/logout', { refresh_token: refreshToken }),
};

export const documentApi = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  registerBlob: (payload) => apiClient.post('/documents/register-blob', payload),
  getDocument: (id) => apiClient.get(`/documents/${id}`),
  listDocuments: (skip = 0, limit = 100) =>
    apiClient.get('/documents/', { params: { skip, limit } }),
  updateDocument: (id, data) => apiClient.put(`/documents/${id}`, data),
  deleteDocument: (id) => apiClient.delete(`/documents/${id}`),
};

export const accessApi = {
  shareDocument: (docId, userIds) =>
    apiClient.post(`/access/documents/${docId}/share`, { user_ids: userIds }),
  createShareLink: (documentIds) =>
    apiClient.post('/access/share-link', { document_ids: documentIds }),
  makePublic: (docId) =>
    apiClient.post(`/access/documents/${docId}/make-public`),
  makePrivate: (docId) =>
    apiClient.post(`/access/documents/${docId}/make-private`),
  getPermissions: (docId) =>
    apiClient.get(`/access/documents/${docId}/permissions`),
};

export default apiClient;
