import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Tab,
  Tabs,
  Alert,
} from '@mui/material';
import {
  Payment,
  Warning,
  CheckCircle,
  Schedule,
  Add,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';

import { formatCurrency, formatDate } from '../../services/api';

// Dados simulados
const mockInvoices = [
  {
    id: 'ap-001',
    supplier_name: 'Fornecedor ABC Ltda',
    invoice_number: 'NF-12345',
    amount: 15000.00,
    due_date: '2024-02-15',
    status: 'pending_approval',
    matching_score: 95.5,
    created_at: '2024-01-20T10:30:00Z',
  },
  {
    id: 'ap-002',
    supplier_name: 'Empresa XYZ S/A',
    invoice_number: 'FAT-67890',
    amount: 8500.50,
    due_date: '2024-02-20',
    status: 'approved',
    matching_score: 98.2,
    created_at: '2024-01-22T14:15:00Z',
  },
  {
    id: 'ap-003',
    supplier_name: 'Serviços DEF',
    invoice_number: 'SRV-11111',
    amount: 3200.00,
    due_date: '2024-01-25',
    status: 'overdue',
    matching_score: 87.3,
    created_at: '2024-01-15T09:45:00Z',
  },
];

const mockExceptions = [
  {
    id: 'exc-001',
    invoice_id: 'ap-004',
    type: 'price_mismatch',
    description: 'Diferença de preço: Fatura R$ 1.500,00 vs PO R$ 1.450,00',
    variance: 50.00,
    severity: 'medium',
  },
  {
    id: 'exc-002',
    invoice_id: 'ap-005',
    type: 'quantity_mismatch',
    description: 'Quantidade faturada (10) maior que recebida (8)',
    variance: 2,
    severity: 'high',
  },
];

function StatusChip({ status }) {
  const statusConfig = {
    pending_approval: { color: 'warning', label: 'Aguardando Aprovação' },
    approved: { color: 'success', label: 'Aprovada' },
    rejected: { color: 'error', label: 'Rejeitada' },
    paid: { color: 'info', label: 'Paga' },
    overdue: { color: 'error', label: 'Vencida' },
  };

  const config = statusConfig[status] || { color: 'default', label: status };

  return (
    <Chip
      label={config.label}
      color={config.color}
      variant="outlined"
      size="small"
    />
  );
}

function AccountsPayable() {
  const [tabValue, setTabValue] = useState(0);

  const columns = [
    {
      field: 'supplier_name',
      headerName: 'Fornecedor',
      flex: 1,
    },
    {
      field: 'invoice_number',
      headerName: 'Nº Fatura',
      width: 120,
    },
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
      renderCell: (params) => <StatusChip status={params.value} />,
    },
    {
      field: 'matching_score',
      headerName: '3-Way Match',
      width: 120,
      renderCell: (params) => {
        const score = params.value;
        const color = score >= 95 ? 'success' : score >= 85 ? 'warning' : 'error';
        return (
          <Chip
            label={`${score}%`}
            color={color}
            variant="outlined"
            size="small"
          />
        );
      },
    },
  ];

  const exceptionColumns = [
    {
      field: 'type',
      headerName: 'Tipo',
      width: 150,
      renderCell: (params) => (
        <Chip
          label={params.value.replace('_', ' ')}
          color="warning"
          variant="outlined"
          size="small"
        />
      ),
    },
    {
      field: 'description',
      headerName: 'Descrição',
      flex: 1,
    },
    {
      field: 'variance',
      headerName: 'Variação',
      width: 100,
      renderCell: (params) => {
        const value = params.value;
        return typeof value === 'number' ? 
          (value > 1 ? formatCurrency(value) : value.toString()) : 
          '-';
      },
    },
    {
      field: 'severity',
      headerName: 'Severidade',
      width: 120,
      renderCell: (params) => {
        const severityConfig = {
          high: { color: 'error', label: 'Alta' },
          medium: { color: 'warning', label: 'Média' },
          low: { color: 'info', label: 'Baixa' },
        };
        const config = severityConfig[params.value];
        return (
          <Chip
            label={config.label}
            color={config.color}
            variant="outlined"
            size="small"
          />
        );
      },
    },
  ];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Contas a Pagar
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gerencie faturas de fornecedores com 3-way matching automático
        </Typography>
      </Box>

      {/* Cards de Resumo */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Total a Pagar
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    {formatCurrency(234800.25)}
                  </Typography>
                </Box>
                <Payment color="primary" sx={{ fontSize: 40 }} />
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
                    Aguardando Aprovação
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    8
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
                    Exceções Detectadas
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    {mockExceptions.length}
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
                    Taxa de Matching
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    94.2%
                  </Typography>
                </Box>
                <CheckCircle color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
            <Tab label="Todas as Faturas" />
            <Tab label="Exceções do 3-Way Matching" />
          </Tabs>
        </Box>

        <CardContent>
          {tabValue === 0 && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Faturas de Fornecedores
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => {/* TODO: Implementar */}}
                >
                  Nova Fatura
                </Button>
              </Box>

              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>3-Way Matching:</strong> As faturas são automaticamente 
                  comparadas com Purchase Orders e Goods Receipts. Scores acima de 95% 
                  são aprovados automaticamente.
                </Typography>
              </Alert>

              <Box sx={{ height: 500, width: '100%' }}>
                <DataGrid
                  rows={mockInvoices}
                  columns={columns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  disableSelectionOnClick
                />
              </Box>
            </>
          )}

          {tabValue === 1 && (
            <>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Exceções do 3-Way Matching
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Discrepâncias detectadas que requerem revisão manual
                </Typography>
              </Box>

              <Alert severity="warning" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Atenção:</strong> {mockExceptions.length} exceções detectadas 
                  requerem revisão manual antes da aprovação.
                </Typography>
              </Alert>

              <Box sx={{ height: 400, width: '100%' }}>
                <DataGrid
                  rows={mockExceptions}
                  columns={exceptionColumns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  disableSelectionOnClick
                />
              </Box>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default AccountsPayable;
