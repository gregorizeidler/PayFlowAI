import axios from 'axios';

// Configuração base do axios
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar respostas e erros
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado ou inválido
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    
    return Promise.reject({
      message: error.response?.data?.message || error.message || 'Erro na requisição',
      status: error.response?.status,
      data: error.response?.data,
    });
  }
);

// Serviços da API

// Dashboard
export const dashboardService = {
  getStats: () => api.get('/dashboard/stats'),
  getChartData: (period = '6m') => api.get(`/dashboard/charts?period=${period}`),
  getRecentActivities: (limit = 10) => api.get(`/dashboard/activities?limit=${limit}`),
};

// Contas a Pagar
export const accountsPayableService = {
  getAll: (params = {}) => api.get('/accounts-payable', { params }),
  getById: (id) => api.get(`/accounts-payable/${id}`),
  create: (data) => api.post('/accounts-payable', data),
  update: (id, data) => api.put(`/accounts-payable/${id}`, data),
  delete: (id) => api.delete(`/accounts-payable/${id}`),
  approve: (id, data) => api.post(`/accounts-payable/${id}/approve`, data),
  reject: (id, data) => api.post(`/accounts-payable/${id}/reject`, data),
  getWorkflowStatus: (id) => api.get(`/accounts-payable/${id}/workflow`),
  getExceptions: (params = {}) => api.get('/accounts-payable/exceptions', { params }),
};

// Contas a Receber
export const accountsReceivableService = {
  getAll: (params = {}) => api.get('/accounts-receivable', { params }),
  getById: (id) => api.get(`/accounts-receivable/${id}`),
  create: (data) => api.post('/accounts-receivable', data),
  update: (id, data) => api.put(`/accounts-receivable/${id}`, data),
  delete: (id) => api.delete(`/accounts-receivable/${id}`),
  sendInvoice: (id) => api.post(`/accounts-receivable/${id}/send`),
  sendDunning: (id, data) => api.post(`/accounts-receivable/${id}/dunning`, data),
  markAsPaid: (id, data) => api.post(`/accounts-receivable/${id}/payment`, data),
  getOverdue: (params = {}) => api.get('/accounts-receivable/overdue', { params }),
  getDunningSchedule: (params = {}) => api.get('/accounts-receivable/dunning-schedule', { params }),
};

// Documentos
export const documentsService = {
  getAll: (params = {}) => api.get('/documents', { params }),
  getById: (id) => api.get(`/documents/${id}`),
  upload: (file, documentType = 'invoice') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    
    return api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  delete: (id) => api.delete(`/documents/${id}`),
  getProcessingStatus: (id) => api.get(`/documents/${id}/status`),
  reprocess: (id) => api.post(`/documents/${id}/reprocess`),
  download: (id) => api.get(`/documents/${id}/download`, { responseType: 'blob' }),
};

// Conciliação Bancária
export const reconciliationService = {
  getAll: (params = {}) => api.get('/reconciliation', { params }),
  getById: (id) => api.get(`/reconciliation/${id}`),
  uploadStatement: (file, bankAccountId = 'default') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank_account_id', bankAccountId);
    
    return api.post('/reconciliation/upload-statement', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  reconcilePeriod: (startDate, endDate, bankAccountId = 'default') => 
    api.post('/reconciliation/reconcile-period', {
      start_date: startDate,
      end_date: endDate,
      bank_account_id: bankAccountId,
    }),
  getUnmatched: (params = {}) => api.get('/reconciliation/unmatched', { params }),
  getDiscrepancies: (params = {}) => api.get('/reconciliation/discrepancies', { params }),
  manualMatch: (transactionId, invoiceId, confidence = 1.0) =>
    api.post('/reconciliation/manual-match', {
      transaction_id: transactionId,
      invoice_id: invoiceId,
      confidence_override: confidence,
    }),
  getMatchingRules: () => api.get('/reconciliation/matching-rules'),
  getStats: () => api.get('/reconciliation/stats'),
};

// Relatórios
export const reportsService = {
  getFinancialSummary: (params = {}) => api.get('/reports/financial-summary', { params }),
  getCashFlow: (params = {}) => api.get('/reports/cash-flow', { params }),
  getAgingReport: (type = 'receivable', params = {}) => 
    api.get(`/reports/aging/${type}`, { params }),
  getReconciliationReport: (params = {}) => api.get('/reports/reconciliation', { params }),
  getProcessingReport: (params = {}) => api.get('/reports/processing', { params }),
  exportReport: (reportType, format = 'pdf', params = {}) =>
    api.get(`/reports/${reportType}/export`, {
      params: { ...params, format },
      responseType: 'blob',
    }),
};

// Fornecedores
export const suppliersService = {
  getAll: (params = {}) => api.get('/suppliers', { params }),
  getById: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  delete: (id) => api.delete(`/suppliers/${id}`),
};

// Clientes
export const customersService = {
  getAll: (params = {}) => api.get('/customers', { params }),
  getById: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
};

// Empresas
export const companiesService = {
  getAll: (params = {}) => api.get('/companies', { params }),
  getById: (id) => api.get(`/companies/${id}`),
  create: (data) => api.post('/companies', data),
  update: (id, data) => api.put(`/companies/${id}`, data),
  delete: (id) => api.delete(`/companies/${id}`),
};

// Autenticação
export const authService = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  register: (userData) => api.post('/auth/register', userData),
  refreshToken: () => api.post('/auth/refresh'),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
};

// Configurações
export const settingsService = {
  getAll: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
  getWorkflowRules: () => api.get('/settings/workflow-rules'),
  updateWorkflowRules: (data) => api.put('/settings/workflow-rules', data),
  getNotificationSettings: () => api.get('/settings/notifications'),
  updateNotificationSettings: (data) => api.put('/settings/notifications', data),
};

// Utilitários
export const utilsService = {
  healthCheck: () => api.get('/health'),
  getSystemStats: () => api.get('/system/stats'),
  validateDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post('/utils/validate-document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Exportar API principal
export default api;

// Helpers para formatação
export const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
};

export const formatDate = (date) => {
  return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
};

export const formatDateTime = (date) => {
  return new Intl.DateTimeFormat('pt-BR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
};
