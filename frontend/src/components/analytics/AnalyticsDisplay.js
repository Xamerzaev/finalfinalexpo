import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PendingIcon from '@mui/icons-material/Pending';
import LinkIcon from '@mui/icons-material/Link';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';

const AnalyticsDisplay = ({ fileId, analysisType }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();

  useEffect(() => {
    if (fileId) {
      fetchAnalyticsData();
    }
  }, [fileId, analysisType]);

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      console.log(`Fetching analytics data for file ${fileId} with type ${analysisType}`);
      const response = await api.get(`/analytics/file/${fileId}?analysis_type=${analysisType}`);
      console.log('Analytics response:', response);
      
      if (response.data && response.data.result) {
        setAnalyticsData(response.data.result);
      } else {
        setError('Данные анализа не найдены');
        showSnackbar('Данные анализа не найдены', 'warning');
      }
    } catch (error) {
      console.error('Error fetching analytics data:', error);
      setError('Ошибка при загрузке данных анализа');
      showSnackbar('Ошибка при загрузке данных анализа', 'error');
    } finally {
      setLoading(false);
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

  if (!analyticsData) {
    return (
      <Alert severity="info" sx={{ mb: 2 }}>
        Нет данных для отображения. Выполните анализ данных.
      </Alert>
    );
  }

  // Проверяем структуру данных и выводим отладочную информацию
  console.log('Analytics data structure:', JSON.stringify(analyticsData, null, 2));

  // Извлекаем данные из ответа API
  const { 
    title, 
    summary, 
    period_data, 
    dynamics, 
    factors, 
    links, 
    completed_tasks, 
    pending_tasks 
  } = analyticsData;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {title || 'Результаты анализа'}
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Резюме
        </Typography>
        <Typography variant="body1">
          {summary || 'Нет данных для отображения'}
        </Typography>
        
        {period_data && (
          <Box sx={{ mt: 2 }}>
            <Chip 
              label={`Период: ${period_data.start_date || '01.01'} - ${period_data.end_date || '31.12'}`} 
              variant="outlined" 
              size="small"
            />
          </Box>
        )}
      </Paper>
      
      <Grid container spacing={3}>
        {/* Динамика показателей */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Динамика показателей
            </Typography>
            
            {dynamics ? (
              <Box>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Всего строк:
                    </Typography>
                    <Typography variant="body1">
                      {dynamics.total_rows || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Всего колонок:
                    </Typography>
                    <Typography variant="body1">
                      {dynamics.total_columns || 0}
                    </Typography>
                  </Grid>
                </Grid>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="subtitle2" gutterBottom>
                  Изменение ключевых метрик:
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {(dynamics.key_metrics_change_percent || 0) >= 0 ? (
                    <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                  ) : (
                    <TrendingDownIcon color="error" sx={{ mr: 1 }} />
                  )}
                  <Typography 
                    variant="h5" 
                    color={(dynamics.key_metrics_change_percent || 0) >= 0 ? 'success.main' : 'error.main'}
                  >
                    {dynamics.key_metrics_change_percent ? 
                      `${dynamics.key_metrics_change_percent.toFixed(2)}%` : 
                      '0%'
                    }
                  </Typography>
                </Box>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="subtitle2" gutterBottom>
                  Средние значения:
                </Typography>
                
                {dynamics.mean && typeof dynamics.mean === 'object' ? (
                  Object.entries(dynamics.mean).map(([key, value]) => (
                    <Box key={key} sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        {key}:
                      </Typography>
                      <Typography variant="body1">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </Typography>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {typeof dynamics.mean === 'number' ? 
                      `Среднее: ${dynamics.mean.toFixed(2)}` : 
                      'Нет данных о средних значениях'
                    }
                  </Typography>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Нет данных о динамике показателей
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Факторы влияния */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Факторы влияния
            </Typography>
            
            {factors ? (
              <Box>
                {factors.key_factors && factors.key_factors.length > 0 ? (
                  <List dense>
                    {factors.key_factors.map((factor, index) => (
                      <ListItem key={index}>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          <TrendingUpIcon color="primary" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={factor} />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Ключевые факторы не выявлены
                  </Typography>
                )}
                
                {factors.missing_values && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Пропущенные значения:
                    </Typography>
                    <Typography variant="body2">
                      {typeof factors.missing_values === 'object' ? 
                        JSON.stringify(factors.missing_values) : 
                        factors.missing_values || 'Нет пропущенных значений'
                      }
                    </Typography>
                  </Box>
                )}
                
                {factors.categorical_data && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Категориальные данные:
                    </Typography>
                    <Typography variant="body2">
                      {typeof factors.categorical_data === 'object' ? 
                        Object.keys(factors.categorical_data).join(', ') : 
                        factors.categorical_data || 'Нет категориальных данных'
                      }
                    </Typography>
                  </Box>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Нет данных о факторах влияния
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Выполненные задачи */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Выполненные задачи
            </Typography>
            
            {completed_tasks && completed_tasks.length > 0 ? (
              <List dense>
                {completed_tasks.map((task, index) => (
                  <ListItem key={index}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckCircleIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={task} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Нет выполненных задач
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Предстоящие задачи */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Предстоящие задачи
            </Typography>
            
            {pending_tasks && pending_tasks.length > 0 ? (
              <List dense>
                {pending_tasks.map((task, index) => (
                  <ListItem key={index}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <PendingIcon color="primary" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={task} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Нет предстоящих задач
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Ссылки */}
        {links && (links.internal.length > 0 || links.external.length > 0) && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Ссылки
              </Typography>
              
              <Grid container spacing={2}>
                {links.internal.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Внутренние ссылки:
                    </Typography>
                    <List dense>
                      {links.internal.map((link, index) => (
                        <ListItem key={index}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <LinkIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={link.title || 'Ссылка'} 
                            secondary={link.description} 
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                )}
                
                {links.external.length > 0 && (
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Внешние ссылки:
                    </Typography>
                    <List dense>
                      {links.external.map((link, index) => (
                        <ListItem key={index} button component="a" href={link.url} target="_blank">
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <LinkIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={link.title || 'Ссылка'} 
                            secondary={link.description} 
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                )}
              </Grid>
            </Paper>
          </Grid>
        )}
      </Grid>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
        <Button 
          variant="outlined" 
          onClick={fetchAnalyticsData}
          startIcon={<TrendingUpIcon />}
        >
          Обновить анализ
        </Button>
      </Box>
    </Box>
  );
};

export default AnalyticsDisplay;
