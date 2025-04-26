import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  TextField, 
  Button, 
  CircularProgress,
  Alert,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';

const Settings = () => {
  const [settings, setSettings] = useState({
    openai_api_key: '',
    default_marketplace: 'ozon',
    use_sample_data: false,
    notification_email: '',
    auto_generate_reports: true
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/settings');
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
      setError('Ошибка при загрузке настроек');
      showSnackbar('Ошибка при загрузке настроек', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, checked } = e.target;
    setSettings({
      ...settings,
      [name]: e.target.type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    
    try {
      await api.put('/settings', settings);
      showSnackbar('Настройки успешно сохранены', 'success');
    } catch (error) {
      console.error('Error saving settings:', error);
      setError('Ошибка при сохранении настроек');
      showSnackbar('Ошибка при сохранении настроек', 'error');
    } finally {
      setSaving(false);
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
        Настройки
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Paper elevation={3} sx={{ p: 3 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Настройки API
              </Typography>
              
              <TextField
                label="API ключ OpenAI"
                name="openai_api_key"
                value={settings.openai_api_key}
                onChange={handleChange}
                fullWidth
                margin="normal"
                type="password"
                helperText="Необходим для анализа данных с использованием ИИ"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Настройки системы
              </Typography>
              
              <FormControl fullWidth margin="normal">
                <InputLabel id="default-marketplace-label">Маркетплейс по умолчанию</InputLabel>
                <Select
                  labelId="default-marketplace-label"
                  name="default_marketplace"
                  value={settings.default_marketplace}
                  label="Маркетплейс по умолчанию"
                  onChange={handleChange}
                >
                  <MenuItem value="ozon">Ozon</MenuItem>
                  <MenuItem value="wildberries">Wildberries</MenuItem>
                </Select>
              </FormControl>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.use_sample_data}
                    onChange={handleChange}
                    name="use_sample_data"
                  />
                }
                label="Использовать тестовые данные"
                sx={{ mt: 2 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.auto_generate_reports}
                    onChange={handleChange}
                    name="auto_generate_reports"
                  />
                }
                label="Автоматически генерировать отчеты"
                sx={{ mt: 1, display: 'block' }}
              />
              
              <TextField
                label="Email для уведомлений"
                name="notification_email"
                value={settings.notification_email}
                onChange={handleChange}
                fullWidth
                margin="normal"
                type="email"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  disabled={saving}
                >
                  {saving ? <CircularProgress size={24} /> : 'Сохранить настройки'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default Settings;
