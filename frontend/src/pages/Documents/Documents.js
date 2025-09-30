import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error,
  Schedule,
  Visibility,
  Download,
  Delete,
  Refresh,
} from '@mui/icons-material';
import { DataGrid } from '@mui/x-data-grid';
import { useDropzone } from 'react-dropzone';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSnackbar } from 'notistack';

import { documentsService, formatDateTime } from '../../services/api';

// Componente de Upload
function DocumentUpload({ onUploadSuccess }) {
  const { enqueueSnackbar } = useSnackbar();
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    // Validar tipo de arquivo
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      enqueueSnackbar('Tipo de arquivo não suportado. Use PDF, JPG ou PNG.', { 
        variant: 'error' 
      });
      return;
    }

    // Validar tamanho (50MB)
    if (file.size > 50 * 1024 * 1024) {
      enqueueSnackbar('Arquivo muito grande. Máximo 50MB.', { variant: 'error' });
      return;
    }

    setUploading(true);
    try {
      const result = await documentsService.upload(file);
      enqueueSnackbar('Documento enviado para processamento!', { variant: 'success' });
      onUploadSuccess(result);
    } catch (error) {
      enqueueSnackbar(error.message || 'Erro ao fazer upload', { variant: 'error' });
    } finally {
      setUploading(false);
    }
  }, [enqueueSnackbar, onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    multiple: false,
  });

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
          Upload de Documentos
        </Typography>
        
        <Box
          {...getRootProps()}
          className={`upload-zone ${isDragActive ? 'active' : ''}`}
          sx={{ mb: 2 }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          
          {uploading ? (
            <>
              <Typography variant="h6" gutterBottom>
                Processando documento...
              </Typography>
              <LinearProgress sx={{ width: '100%', maxWidth: 300 }} />
            </>
          ) : (
            <>
              <Typography variant="h6" gutterBottom>
                {isDragActive
                  ? 'Solte o arquivo aqui...'
                  : 'Arraste um arquivo ou clique para selecionar'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Suporta PDF, JPG, PNG (máx. 50MB)
              </Typography>
            </>
          )}
        </Box>

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Processamento Automático:</strong> Seus documentos serão processados 
            automaticamente usando OCR e NLP para extrair dados estruturados.
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );
}

// Status do documento
function DocumentStatus({ status }) {
  const statusConfig = {
    pending: { color: 'warning', icon: <Schedule />, label: 'Processando' },
    completed: { color: 'success', icon: <CheckCircle />, label: 'Concluído' },
    failed: { color: 'error', icon: <Error />, label: 'Erro' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <Chip
      icon={config.icon}
      label={config.label}
      color={config.color}
      variant="outlined"
      size="small"
    />
  );
}

function Documents() {
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Buscar documentos
  const { data: documents = [], isLoading, refetch } = useQuery(
    'documents',
    () => documentsService.getAll(),
    {
      refetchInterval: 5000, // Atualizar a cada 5 segundos
    }
  );

  // Mutation para deletar documento
  const deleteMutation = useMutation(
    (id) => documentsService.delete(id),
    {
      onSuccess: () => {
        enqueueSnackbar('Documento excluído com sucesso!', { variant: 'success' });
        queryClient.invalidateQueries('documents');
      },
      onError: (error) => {
        enqueueSnackbar(error.message || 'Erro ao excluir documento', { variant: 'error' });
      },
    }
  );

  // Mutation para reprocessar documento
  const reprocessMutation = useMutation(
    (id) => documentsService.reprocess(id),
    {
      onSuccess: () => {
        enqueueSnackbar('Documento enviado para reprocessamento!', { variant: 'success' });
        queryClient.invalidateQueries('documents');
      },
      onError: (error) => {
        enqueueSnackbar(error.message || 'Erro ao reprocessar documento', { variant: 'error' });
      },
    }
  );

  const handleUploadSuccess = () => {
    queryClient.invalidateQueries('documents');
  };

  const handleViewDetails = (document) => {
    setSelectedDocument(document);
    setDetailsOpen(true);
  };

  const handleDownload = async (document) => {
    try {
      const blob = await documentsService.download(document.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = document.original_filename || `document_${document.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      enqueueSnackbar('Erro ao baixar documento', { variant: 'error' });
    }
  };

  // Colunas da tabela
  const columns = [
    {
      field: 'original_filename',
      headerName: 'Nome do Arquivo',
      flex: 1,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Description color="action" />
          <Typography variant="body2">{params.value}</Typography>
        </Box>
      ),
    },
    {
      field: 'document_type',
      headerName: 'Tipo',
      width: 120,
      renderCell: (params) => (
        <Chip label={params.value || 'Documento'} size="small" />
      ),
    },
    {
      field: 'processing_status',
      headerName: 'Status',
      width: 130,
      renderCell: (params) => <DocumentStatus status={params.value} />,
    },
    {
      field: 'file_size',
      headerName: 'Tamanho',
      width: 100,
      renderCell: (params) => {
        const size = params.value;
        if (size < 1024) return `${size} B`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
        return `${(size / (1024 * 1024)).toFixed(1)} MB`;
      },
    },
    {
      field: 'created_at',
      headerName: 'Enviado em',
      width: 150,
      renderCell: (params) => formatDateTime(params.value),
    },
    {
      field: 'ocr_confidence',
      headerName: 'Confiança OCR',
      width: 120,
      renderCell: (params) => {
        const confidence = params.value;
        if (!confidence) return '-';
        
        const percentage = Math.round(confidence * 100);
        const color = percentage >= 90 ? 'success' : percentage >= 70 ? 'warning' : 'error';
        
        return (
          <Chip
            label={`${percentage}%`}
            color={color}
            variant="outlined"
            size="small"
          />
        );
      },
    },
    {
      field: 'actions',
      headerName: 'Ações',
      width: 150,
      sortable: false,
      renderCell: (params) => (
        <Box>
          <Tooltip title="Ver detalhes">
            <IconButton
              size="small"
              onClick={() => handleViewDetails(params.row)}
            >
              <Visibility />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Download">
            <IconButton
              size="small"
              onClick={() => handleDownload(params.row)}
            >
              <Download />
            </IconButton>
          </Tooltip>
          
          {params.row.processing_status === 'failed' && (
            <Tooltip title="Reprocessar">
              <IconButton
                size="small"
                onClick={() => reprocessMutation.mutate(params.row.id)}
                disabled={reprocessMutation.isLoading}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          )}
          
          <Tooltip title="Excluir">
            <IconButton
              size="small"
              color="error"
              onClick={() => deleteMutation.mutate(params.row.id)}
              disabled={deleteMutation.isLoading}
            >
              <Delete />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Documentos
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Gerencie e processe documentos com OCR automático
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Upload */}
        <Grid item xs={12} lg={4}>
          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          
          {/* Estatísticas */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Estatísticas
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Total de Documentos</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {documents.length}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Processados</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {documents.filter(d => d.processing_status === 'completed').length}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Em Processamento</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {documents.filter(d => d.processing_status === 'pending').length}
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Com Erro</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: 'error.main' }}>
                    {documents.filter(d => d.processing_status === 'failed').length}
                  </Typography>
                </Box>
              </Box>
              
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Refresh />}
                onClick={() => refetch()}
                disabled={isLoading}
              >
                Atualizar Lista
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Lista de Documentos */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Documentos Enviados
              </Typography>
              
              <Box sx={{ height: 600, width: '100%' }}>
                <DataGrid
                  rows={documents}
                  columns={columns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  loading={isLoading}
                  disableSelectionOnClick
                  sx={{
                    '& .MuiDataGrid-row:hover': {
                      backgroundColor: 'action.hover',
                    },
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Dialog de Detalhes */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Documento
        </DialogTitle>
        <DialogContent>
          {selectedDocument && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Nome do Arquivo
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {selectedDocument.original_filename}
                  </Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Status do Processamento
                  </Typography>
                  <DocumentStatus status={selectedDocument.processing_status} />
                </Grid>
                
                {selectedDocument.extracted_data && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      Dados Extraídos
                    </Typography>
                    <Box
                      component="pre"
                      sx={{
                        backgroundColor: 'grey.100',
                        p: 2,
                        borderRadius: 1,
                        fontSize: '0.875rem',
                        overflow: 'auto',
                        maxHeight: 300,
                      }}
                    >
                      {JSON.stringify(selectedDocument.extracted_data, null, 2)}
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Fechar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Documents;
