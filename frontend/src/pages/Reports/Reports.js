import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Alert,
} from '@mui/material';
import {
  GetApp,
  Assessment,
  TrendingUp,
  AccountBalance,
} from '@mui/icons-material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

const mockCashFlowData = [
  { month: 'Jan', inflow: 65000, outflow: 45000 },
  { month: 'Fev', inflow: 75000, outflow: 52000 },
  { month: 'Mar', inflow: 85000, outflow: 48000 },
  { month: 'Abr', inflow: 78000, outflow: 55000 },
  { month: 'Mai', inflow: 92000, outflow: 61000 },
  { month: 'Jun', inflow: 88000, outflow: 58000 },
];

function Reports() {
  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Relatórios
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Análises financeiras e relatórios detalhados
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Fluxo de Caixa
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Relatório detalhado de entradas e saídas
              </Typography>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<GetApp />}
              >
                Baixar PDF
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Aging Report
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Análise de vencimentos por período
              </Typography>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<GetApp />}
              >
                Baixar Excel
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Conciliação
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Relatório de conciliação bancária
              </Typography>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<GetApp />}
              >
                Baixar PDF
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Processamento
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Estatísticas de OCR e workflows
              </Typography>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<GetApp />}
              >
                Baixar PDF
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Fluxo de Caixa - Últimos 6 Meses
              </Typography>
              
              <Box sx={{ height: 400, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={mockCashFlowData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip 
                      formatter={(value) => [
                        value.toLocaleString('pt-BR', { 
                          style: 'currency', 
                          currency: 'BRL' 
                        }),
                      ]}
                    />
                    <Bar dataKey="inflow" fill="#4caf50" name="Entradas" />
                    <Bar dataKey="outflow" fill="#f44336" name="Saídas" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Resumo Financeiro
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Total Recebido</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
                    R$ 485.600,50
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Total Pago</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                    R$ 234.800,25
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Saldo Líquido</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    R$ 250.800,25
                  </Typography>
                </Box>
              </Box>

              <Alert severity="success">
                <Typography variant="body2">
                  <strong>+15.3%</strong> vs mês anterior
                </Typography>
              </Alert>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Indicadores de Performance
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Taxa de Cobrança</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    94.2%
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Tempo Médio de Pagamento</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    28.5 dias
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Precisão do OCR</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    96.8%
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Auto-matching</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    93.2%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Reports;
