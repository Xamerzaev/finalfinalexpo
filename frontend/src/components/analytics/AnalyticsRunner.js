import React, { useState } from 'react';
import { Box, Button, CircularProgress, Typography, Paper, Snackbar, Alert } from '@mui/material';
import api from '../../services/api';
import AnalyticsDisplay from './AnalyticsDisplay';

/**
 * Компонент для запуска анализа данных и отображения результатов
 * 
 * @param {Object} props - Свойства компонента
 * @param {number} props.fileId - ID файла для анализа
 * @param {string} props.analysisType - Тип анализа (trends, competitors, metrics)
 */
const AnalyticsRunner = ({ fileId, analysisType = 'trends' }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('info');
  const [taskId, setTaskId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(Date.now());

  // Функция для отображения уведомлений
  const showSnackbar = (message, severity = 'info') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  const runAnalysis = async () => {
    if (!fileId) {
      setError('Файл не выбран');
      showSnackbar('Файл не выбран', 'error');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysisComplete(false);
    
    console.log('Запуск анализа с параметрами:', {
      file_id: fileId,
      analysis_type: analysisType
    });
    
    showSnackbar('Запуск анализа...', 'info');

    try {
      // Запускаем анализ данных
      console.log('Отправка POST запроса на /analytics/analyze');
      const response = await api.post('/analytics/analyze', {
        file_id: fileId,
        analysis_type: analysisType,
        parameters: {}
      });

      console.log('Ответ от сервера:', response.data);
      
      if (response.data && response.data.task_id) {
        setTaskId(response.data.task_id);
        showSnackbar('Анализ запущен. Это может занять некоторое время.', 'info');
      }
      
      // Обновляем ключ для компонента AnalyticsDisplay, чтобы он перезагрузил данные
      setRefreshKey(Date.now());
      setAnalysisComplete(true);
    } catch (err) {
      console.error('Ошибка при запуске анализа:', err);
      
      setError(err.response?.data?.detail || 'Ошибка при запуске анализа');
      showSnackbar(err.response?.data?.detail || 'Ошибка при запуске анализа', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6">Анализ данных</Typography>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={runAnalysis}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
          >
            {loading ? 'Анализ...' : 'Запустить анализ'}
          </Button>
        </Box>
        
        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
        
        <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
          {loading ? 
            'Запуск анализа данных. Пожалуйста, подождите...' : 
            'Нажмите кнопку "Запустить анализ" для анализа данных с помощью искусственного интеллекта.'}
        </Typography>
        
        {taskId && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            ID задачи: {taskId}
          </Typography>
        )}
      </Paper>

      {/* Отображаем результаты анализа */}
      <AnalyticsDisplay 
        fileId={fileId} 
        analysisType={analysisType} 
        key={refreshKey} 
      />
      
      {/* Уведомления */}
      <Snackbar 
        open={snackbarOpen} 
        autoHideDuration={6000} 
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AnalyticsRunner;
