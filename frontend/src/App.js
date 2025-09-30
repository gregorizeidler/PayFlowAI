import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';

// Layout
import Layout from './components/Layout/Layout';

// Pages
import Dashboard from './pages/Dashboard/Dashboard';
import AccountsPayable from './pages/AccountsPayable/AccountsPayable';
import AccountsReceivable from './pages/AccountsReceivable/AccountsReceivable';
import Documents from './pages/Documents/Documents';
import Reconciliation from './pages/Reconciliation/Reconciliation';
import Reports from './pages/Reports/Reports';
import Settings from './pages/Settings/Settings';

function App() {
  return (
    <Box sx={{ display: 'flex' }}>
      <Layout>
        <Routes>
          {/* Rota padrão - redirecionar para dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* Páginas principais */}
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/accounts-payable" element={<AccountsPayable />} />
          <Route path="/accounts-receivable" element={<AccountsReceivable />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="/reconciliation" element={<Reconciliation />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          
          {/* Rota 404 - redirecionar para dashboard */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;
