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
import { Link } from 'react-router-dom';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';

const ReportsList = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/reports');
      setReports(response.data);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setError('Ошибка при загрузке отчетов');
      showSnackbar('Ошибка при загрузке отчетов', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот отчет?')) {
      return;
    }
    
    try {
      await api.delete(`/reports/${reportId}`);
      showSnackbar('Отчет успешно удален', 'success');
      fetchReports(); // Обновляем список отчетов
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

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Отчеты
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {reports.length > 0 ? (
          reports.map((report) => (
            <Grid item xs={12} key={report.id}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="h6">
                      {report.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Кабинет: {report.cabinet_name} | 
                      Период: {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()} | 
                      Создан: {new Date(report.created_at).toLocaleString()}
                    </Typography>
                  </Box>
                  <Box>
                    <Button 
                      variant="outlined" 
                      component={Link} 
                      to={`/reports/${report.id}`}
                      sx={{ mr: 1 }}
                    >
                      Просмотреть
                    </Button>
                    <Button 
                      variant="outlined" 
                      color="error"
                      onClick={() => handleDeleteReport(report.id)}
                    >
                      Удалить
                    </Button>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          ))
        ) : (
          <Grid item xs={12}>
            <Alert severity="info">
              У вас пока нет отчетов. Загрузите данные и проведите анализ, чтобы создать отчет.
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ReportsList;
