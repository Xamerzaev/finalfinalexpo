import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  CircularProgress,
  Alert,
  Divider
} from '@mui/material';
import { useParams, useHistory } from 'react-router-dom';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';
import AnalyticsDisplay from '../analytics/AnalyticsDisplay';

const ReportDetail = () => {
  const { reportId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();
  const history = useHistory();

  useEffect(() => {
    fetchReportData();
  }, [reportId]);

  const fetchReportData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get(`/reports/${reportId}`);
      setReport(response.data);
    } catch (error) {
      console.error('Error fetching report:', error);
      setError('Ошибка при загрузке отчета');
      showSnackbar('Ошибка при загрузке отчета', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить этот отчет?')) {
      return;
    }
    
    try {
      await api.delete(`/reports/${reportId}`);
      showSnackbar('Отчет успешно удален', 'success');
      history.push('/reports');
    } catch (error) {
      console.error('Error deleting report:', error);
      showSnackbar('Ошибка при удалении отчета', 'error');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!report) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        Отчет не найден
      </Alert>
    );
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          {report.title}
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            color="error"
            onClick={handleDeleteReport}
          >
            Удалить отчет
          </Button>
        </Box>
      </Box>
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Кабинет: {report.cabinet_name} | 
          Маркетплейс: {report.marketplace === 'ozon' ? 'Ozon' : 'Wildberries'} | 
          Период: {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()} | 
          Создан: {new Date(report.created_at).toLocaleString()}
        </Typography>
        
        <Divider sx={{ my: 2 }} />
        
        <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
          {report.content}
        </Typography>
      </Paper>
      
      <AnalyticsDisplay reportId={reportId} />
    </Box>
  );
};

export default ReportDetail;
