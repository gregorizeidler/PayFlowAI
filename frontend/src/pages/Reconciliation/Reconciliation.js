import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Alert,
  Chip,
} from '@mui/material';
import {
  AccountBalance,
  CheckCircle,
  Warning,
  CloudUpload,
  Assessment,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';

import { formatCurrency, formatDate } from '../../services/api';

const mockTransactions = [
  {
    id: 'txn-001',
    date: '2024-01-18',
    description: 'TED RECEBIDA EMPRESA ABC',
    amount: 1500.00,
    type: 'credit',
    matched: true,
    confidence: 0.95,
  },
  {
    id: 'txn-002',
    date: '2024-01-19',
    description: 'PAGAMENTO FORNECEDOR XYZ',
    amount: -850.00,
    type: 'debit',
    matched: false,
    confidence: 0.65,
  },
];

function MatchStatus({ matched, confidence }) {
  if (matched) {
    return <Chip label="Conciliada" color="success" variant="outlined" size="small" />;
  }
  
  const confidencePercent = Math.round(confidence * 100);
  const color = confidencePercent >= 80 ? 'warning' : 'error';
  
  return (
    <Chip 
      label={`Não conciliada (${confidencePercent}%)`} 
      color={color} 
      variant="outlined" 
      size="small" 
    />
  );
}

function Reconciliation() {
  const columns = [
    { 
      field: 'date', 
      headerName: 'Data', 
      width: 120,
      renderCell: (params) => formatDate(params.value),
    },
    { field: 'description', headerName: 'Descrição', flex: 1 },
    { 
      field: 'amount', 
      headerName: 'Valor', 
      width: 130,
      renderCell: (params) => (
        <Typography
          sx={{
            color: params.value > 0 ? 'success.main' : 'error.main',
            fontWeight: 600,
          }}
        >
          {formatCurrency(params.value)}
        </Typography>
      ),
    },
    { 
      field: 'type', 
      headerName: 'Tipo', 
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value === 'credit' ? 'Crédito' : 'Débito'}
          color={params.value === 'credit' ? 'success' : 'error'}
          variant="outlined"
          size="small"
        />
      ),
    },
    { 
      field: 'matched', 
      headerName: 'Status', 
      width: 180,
      renderCell: (params) => (
        <MatchStatus matched={params.value} confidence={params.row.confidence} />
      ),
    },
  ];

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Conciliação Bancária
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Concilie automaticamente extratos bancários com faturas usando fuzzy matching
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="body2">
                    Transações Analisadas
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    2,847
                  </Typography>
                </Box>
                <AccountBalance color="primary" sx={{ fontSize: 40 }} />
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
                    Auto Conciliadas
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    2,654
                  </Typography>
                </Box>
                <CheckCircle color="success" sx={{ fontSize: 40 }} />
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
                    Revisão Manual
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    193
                  </Typography>
                </Box>
                <Warning color="warning" sx={{ fontSize: 40 }} />
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
                    Precisão do Matching
                  </Typography>
                  <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
                    93.2%
                  </Typography>
                </Box>
                <Assessment color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Transações Bancárias
              </Typography>
              
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Fuzzy Matching:</strong> Algoritmos avançados comparam transações 
                  bancárias com faturas usando similaridade de valor, data e descrição.
                </Typography>
              </Alert>

              <Box sx={{ height: 500, width: '100%' }}>
                <DataGrid
                  rows={mockTransactions}
                  columns={columns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  disableSelectionOnClick
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Upload de Extrato
              </Typography>
              
              <Box
                sx={{
                  border: '2px dashed #ccc',
                  borderRadius: 2,
                  p: 3,
                  textAlign: 'center',
                  cursor: 'pointer',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'action.hover',
                  },
                }}
              >
                <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="body1" gutterBottom>
                  Arraste um extrato ou clique para selecionar
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Suporta OFX, CSV, PDF
                </Typography>
              </Box>

              <Button
                variant="contained"
                fullWidth
                sx={{ mt: 2 }}
                startIcon={<CloudUpload />}
              >
                Selecionar Arquivo
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Algoritmos de Matching
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Valor (40% peso)
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Data (25% peso)
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Descrição (25% peso)
                </Typography>
                <Typography variant="body2">
                  Referência (10% peso)
                </Typography>
              </Box>

              <Alert severity="success">
                <Typography variant="body2">
                  <strong>Auto-match:</strong> Confiança ≥ 95%<br />
                  <strong>Revisão manual:</strong> Confiança 70-94%<br />
                  <strong>Rejeitado:</strong> Confiança &lt; 70%
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Reconciliation;
