import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Alert,
} from '@mui/material';
import {
  Receipt,
  Schedule,
  Warning,
  TrendingUp,
  Add,
  Send,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';

import { formatCurrency, formatDate } from '../../services/api';

const mockReceivables = [
  {
    id: 'ar-001',
    customer_name: 'Cliente ABC Ltda',
    invoice_number: 'INV-001',
    amount: 15000.00,
    due_date: '2024-02-15',
    status: 'active',
    days_overdue: 0,
  },
  {
    id: 'ar-002',
    customer_name: 'Empresa XYZ S/A',
    invoice_number: 'INV-002',
    amount: 8500.50,
    due_date: '2024-01-20',
    status: 'overdue',
    days_overdue: 15,
  },
];

function StatusChip({ status, daysOverdue }) {
  if (status === 'overdue') {
    return <Chip label={`Vencida (${daysOverdue}d)`} color="error" variant="outlined" size="small" />;
  }
  
  const statusConfig = {
    active: { color: 'success', label: 'Ativa' },
    paid: { color: 'info', label: 'Paga' },
  };

  const config = statusConfig[status] || { color: 'default', label: status };
  return <Chip label={config.label} color={config.color} variant="outlined" size="small" />;
}

function AccountsReceivable() {
  const columns = [
    { field: 'customer_name', headerName: 'Cliente', flex: 1 },
    { field: 'invoice_number', headerName: 'Nº Fatura', width: 120 },
    { 
      field: 'amount', 
      headerName: 'Valor', 
      width: 130,
      renderCell: (params) => formatCurrency(params.value),
    },
    { 
      field: 'due_date', 
      headerName: 'Vencimento', 
      width: 120,
      renderCell: (params) => formatDate(params.value),
    },
    { 
      field: 'status', 
      headerName: 'Status', 
      width: 150,
      renderCell: (params) => (
        <StatusChip status={params.value} daysOverdue={params.row.days_overdue} />
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Contas a Receber
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gerencie faturas de clientes com cobrança automatizada
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total a Receber
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    {formatCurrency(485600.50)}
                  </Typography>
                </Box>
                <Receipt color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Vencendo Hoje
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    5
                  </Typography>
                </Box>
                <Schedule color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Em Atraso
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    {formatCurrency(45800.25)}
                  </Typography>
                </Box>
                <Warning color="error" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Taxa de Cobrança
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    94.2%
                  </Typography>
                </Box>
                <TrendingUp color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Faturas de Clientes
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="outlined" startIcon={<Send />}>
                Enviar Cobrança
              </Button>
              <Button variant="contained" startIcon={<Add />}>
                Nova Fatura
              </Button>
            </Box>
          </Box>

          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Cobrança Automatizada:</strong> Lembretes são enviados automaticamente 
              5 dias antes do vencimento, no vencimento e após 7, 15 e 30 dias de atraso.
            </Typography>
          </Alert>

          <Box sx={{ height: 500, width: '100%' }}>
            <DataGrid
              rows={mockReceivables}
              columns={columns}
              pageSize={10}
              rowsPerPageOptions={[10, 25, 50]}
              disableSelectionOnClick
            />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default AccountsReceivable;
