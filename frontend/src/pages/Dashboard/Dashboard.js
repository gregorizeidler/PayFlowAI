import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  IconButton,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Receipt,
  Payment,
  AccountBalance,
  Warning,
  CheckCircle,
  Schedule,
  AttachMoney,
  Description,
  Visibility,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts';

import { useQuery } from 'react-query';
import { dashboardService } from '../../services/api';

// Dados simulados para demonstração
const mockData = {
  summary: {
    totalReceivables: 485600.50,
    totalPayables: 234800.25,
    overdueAmount: 45800.25,
    cashFlow: 250800.25,
  },
  trends: [
    { month: 'Jan', receivables: 65000, payables: 45000 },
    { month: 'Fev', receivables: 75000, payables: 52000 },
    { month: 'Mar', receivables: 85000, payables: 48000 },
    { month: 'Abr', receivables: 78000, payables: 55000 },
    { month: 'Mai', receivables: 92000, payables: 61000 },
    { month: 'Jun', receivables: 88000, payables: 58000 },
  ],
  statusDistribution: [
    { name: 'Em Dia', value: 75, color: '#4caf50' },
    { name: 'Vencendo', value: 15, color: '#ff9800' },
    { name: 'Vencidas', value: 10, color: '#f44336' },
  ],
  recentActivities: [
    {
      id: 1,
      type: 'payment_received',
      description: 'Pagamento recebido - Cliente ABC Ltda',
      amount: 15000,
      time: '2 horas atrás',
    },
    {
      id: 2,
      type: 'invoice_created',
      description: 'Nova fatura criada - Empresa XYZ',
      amount: 8500,
      time: '4 horas atrás',
    },
    {
      id: 3,
      type: 'payment_sent',
      description: 'Pagamento enviado - Fornecedor DEF',
      amount: -5200,
      time: '6 horas atrás',
    },
    {
      id: 4,
      type: 'document_processed',
      description: 'Documento processado via OCR',
      time: '8 horas atrás',
    },
  ],
};

function StatCard({ title, value, change, icon, color = 'primary' }) {
  const isPositive = change >= 0;
  
  return (
    <Card className="dashboard-card">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 600 }}>
              {typeof value === 'number' ? 
                value.toLocaleString('pt-BR', { 
                  style: 'currency', 
                  currency: 'BRL' 
                }) : 
                value
              }
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
              {isPositive ? (
                <TrendingUp sx={{ color: 'success.main', mr: 0.5 }} />
              ) : (
                <TrendingDown sx={{ color: 'error.main', mr: 0.5 }} />
              )}
              <Typography
                variant="body2"
                sx={{
                  color: isPositive ? 'success.main' : 'error.main',
                  fontWeight: 500,
                }}
              >
                {Math.abs(change)}% vs mês anterior
              </Typography>
            </Box>
          </Box>
          <Avatar
            sx={{
              bgcolor: `${color}.main`,
              width: 56,
              height: 56,
            }}
          >
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );
}

function ActivityIcon({ type }) {
  const iconProps = { sx: { color: 'white' } };
  
  switch (type) {
    case 'payment_received':
      return <Receipt {...iconProps} />;
    case 'payment_sent':
      return <Payment {...iconProps} />;
    case 'invoice_created':
      return <Description {...iconProps} />;
    case 'document_processed':
      return <CheckCircle {...iconProps} />;
    default:
      return <Schedule {...iconProps} />;
  }
}

function ActivityColor(type) {
  switch (type) {
    case 'payment_received':
      return '#4caf50';
    case 'payment_sent':
      return '#f44336';
    case 'invoice_created':
      return '#2196f3';
    case 'document_processed':
      return '#ff9800';
    default:
      return '#9e9e9e';
  }
}

function Dashboard() {
  // Em um app real, isso viria da API
  const { data: dashboardData, isLoading } = useQuery(
    'dashboard',
    () => Promise.resolve(mockData),
    {
      refetchInterval: 30000, // Atualizar a cada 30 segundos
    }
  );

  if (isLoading) {
    return (
      <Box sx={{ width: '100%' }}>
        <LinearProgress />
      </Box>
    );
  }

  const { summary, trends, statusDistribution, recentActivities } = dashboardData;

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Dashboard Financeiro
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Visão geral das suas finanças em tempo real
        </Typography>
      </Box>

      {/* Cards de Resumo */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Contas a Receber"
            value={summary.totalReceivables}
            change={12.5}
            icon={<Receipt />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Contas a Pagar"
            value={summary.totalPayables}
            change={-5.2}
            icon={<Payment />}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Valores em Atraso"
            value={summary.overdueAmount}
            change={-8.1}
            icon={<Warning />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Fluxo de Caixa"
            value={summary.cashFlow}
            change={15.3}
            icon={<AccountBalance />}
            color="primary"
          />
        </Grid>
      </Grid>

      {/* Gráficos */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Tendência Mensal */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Tendência Mensal
              </Typography>
              <Box className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trends}>
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
                    <Line
                      type="monotone"
                      dataKey="receivables"
                      stroke="#4caf50"
                      strokeWidth={3}
                      name="Recebimentos"
                    />
                    <Line
                      type="monotone"
                      dataKey="payables"
                      stroke="#f44336"
                      strokeWidth={3}
                      name="Pagamentos"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Status das Faturas */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Status das Faturas
              </Typography>
              <Box sx={{ height: 250, display: 'flex', alignItems: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={statusDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {statusDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value}%`]} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
              <Box sx={{ mt: 2 }}>
                {statusDistribution.map((item) => (
                  <Box
                    key={item.name}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      mb: 1,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          bgcolor: item.color,
                          borderRadius: '50%',
                          mr: 1,
                        }}
                      />
                      <Typography variant="body2">{item.name}</Typography>
                    </Box>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {item.value}%
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Atividades Recentes */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Atividades Recentes
              </Typography>
              <List>
                {recentActivities.map((activity) => (
                  <ListItem
                    key={activity.id}
                    sx={{
                      px: 0,
                      '&:not(:last-child)': {
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                      },
                    }}
                  >
                    <ListItemIcon>
                      <Avatar
                        sx={{
                          bgcolor: ActivityColor(activity.type),
                          width: 40,
                          height: 40,
                        }}
                      >
                        <ActivityIcon type={activity.type} />
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.description}
                      secondary={activity.time}
                      sx={{ ml: 1 }}
                    />
                    {activity.amount && (
                      <Box sx={{ textAlign: 'right' }}>
                        <Typography
                          variant="body2"
                          sx={{
                            fontWeight: 600,
                            color: activity.amount > 0 ? 'success.main' : 'error.main',
                          }}
                        >
                          {activity.amount.toLocaleString('pt-BR', {
                            style: 'currency',
                            currency: 'BRL',
                          })}
                        </Typography>
                      </Box>
                    )}
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Alertas e Notificações */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Alertas e Notificações
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Chip
                  icon={<Warning />}
                  label="12 faturas vencendo em 3 dias"
                  color="warning"
                  variant="outlined"
                  sx={{ mb: 1, mr: 1 }}
                />
                <Chip
                  icon={<CheckCircle />}
                  label="8 documentos processados hoje"
                  color="success"
                  variant="outlined"
                  sx={{ mb: 1, mr: 1 }}
                />
                <Chip
                  icon={<Schedule />}
                  label="Conciliação bancária pendente"
                  color="info"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Resumo dos processos automatizados:
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">OCR Processing</Typography>
                  <Typography variant="body2">94%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={94} sx={{ mb: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Auto Matching</Typography>
                  <Typography variant="body2">87%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={87} sx={{ mb: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Payment Processing</Typography>
                  <Typography variant="body2">98%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={98} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
