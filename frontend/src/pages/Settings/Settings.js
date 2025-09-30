import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Divider,
  Alert,
} from '@mui/material';
import {
  Save,
  Notifications,
  Security,
  Integration,
  AutoMode,
} from '@mui/icons-material';

function Settings() {
  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Configurações
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure o comportamento do sistema de automação financeira
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={6}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <AutoMode sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Automação de Workflows
                </Typography>
              </Box>

              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Aprovação automática (valores até R$ 1.000)"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="3-Way Matching automático"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Processamento OCR automático"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Conciliação bancária automática"
                sx={{ mb: 3, display: 'block' }}
              />

              <Divider sx={{ my: 3 }} />

              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Limites de Aprovação
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Aprovação Automática"
                    defaultValue="1000"
                    fullWidth
                    size="small"
                    InputProps={{
                      startAdornment: 'R$ ',
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Aprovação Gerencial"
                    defaultValue="10000"
                    fullWidth
                    size="small"
                    InputProps={{
                      startAdornment: 'R$ ',
                    }}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Integration sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Integrações
                </Typography>
              </Box>

              <FormControlLabel
                control={<Switch defaultChecked />}
                label="API do Banco Central (PIX)"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch />}
                label="ERP Externo"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Gateway de Pagamento"
                sx={{ mb: 3, display: 'block' }}
              />

              <Alert severity="info">
                <Typography variant="body2">
                  Configure as credenciais das integrações nas variáveis de ambiente
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={6}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Notifications sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Notificações
                </Typography>
              </Box>

              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Email para exceções do 3-Way Matching"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Email para faturas vencendo"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch />}
                label="SMS para valores altos"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Relatórios diários por email"
                sx={{ mb: 3, display: 'block' }}
              />

              <TextField
                label="Email para notificações"
                defaultValue="admin@empresa.com"
                fullWidth
                size="small"
                sx={{ mb: 2 }}
              />
              
              <TextField
                label="Telefone para SMS"
                defaultValue="+55 11 99999-9999"
                fullWidth
                size="small"
              />
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Security sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Segurança
                </Typography>
              </Box>

              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Autenticação de dois fatores"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch defaultChecked />}
                label="Log de auditoria detalhado"
                sx={{ mb: 2, display: 'block' }}
              />
              
              <FormControlLabel
                control={<Switch />}
                label="Criptografia avançada"
                sx={{ mb: 3, display: 'block' }}
              />

              <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                Tolerâncias de Matching
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Tolerância de Valor (%)"
                    defaultValue="2.0"
                    fullWidth
                    size="small"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Tolerância de Data (dias)"
                    defaultValue="7"
                    fullWidth
                    size="small"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Save />}
        >
          Salvar Configurações
        </Button>
      </Box>
    </Box>
  );
}

export default Settings;
