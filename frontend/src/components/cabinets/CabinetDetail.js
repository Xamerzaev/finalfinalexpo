import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import FileUpload from '../common/FileUpload';
import AnalyticsDisplay from '../analytics/AnalyticsDisplay';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';

// Компонент для отображения списка файлов
const FilesList = ({ files, onRefresh, onAnalyzeFile }) => {
  const { showSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(false);

  const handleDeleteFile = async (fileId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот файл?')) {
      return;
    }

    setLoading(true);
    try {
      await api.delete(`/files/files/${fileId}`);
      showSnackbar('Файл успешно удален', 'success');
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Error deleting file:', error);
      showSnackbar('Ошибка при удалении файла', 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!files || files.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Нет загруженных файлов
      </Alert>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        Загруженные файлы
      </Typography>
      <Grid container spacing={2}>
        {files.map((file) => (
          <Grid item xs={12} key={file.id}>
            <Paper sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="subtitle1">
                  {file.original_filename}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Тип: {file.file_type === 'metrics' ? 'Метрики' : 'Отчетная таблица'} | 
                  Загружен: {new Date(file.upload_date).toLocaleString()} | 
                  Статус: {file.processed ? 'Обработан' : 'В обработке'}
                </Typography>
              </Box>
              <Box>
                {file.processed && (
                  <Button 
                    color="primary" 
                    onClick={() => onAnalyzeFile(file.id)}
                    sx={{ mr: 1 }}
                  >
                    Анализировать
                  </Button>
                )}
                <Button 
                  color="error" 
                  onClick={() => handleDeleteFile(file.id)}
                  disabled={loading}
                >
                  Удалить
                </Button>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

const CabinetDetail = ({ match }) => {
  const cabinetId = match.params.cabinetId;
  const [cabinet, setCabinet] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);
  const { showSnackbar } = useSnackbar();
  
  // Состояние для диалога анализа
  const [analysisDialogOpen, setAnalysisDialogOpen] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [analysisType, setAnalysisType] = useState('trends');

  useEffect(() => {
    fetchCabinetData();
    fetchFiles();
  }, [cabinetId]);

  const fetchCabinetData = async () => {
    try {
      const response = await api.get(`/cabinets/${cabinetId}`);
      setCabinet(response.data);
    } catch (error) {
      console.error('Error fetching cabinet:', error);
      setError('Ошибка при загрузке данных кабинета');
      showSnackbar('Ошибка при загрузке данных кабинета', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchFiles = async () => {
    try {
      const response = await api.get(`/files/files?cabinet_id=${cabinetId}`);
      setFiles(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
      showSnackbar('Ошибка при загрузке списка файлов', 'error');
    }
  };

  const handleUploadSuccess = () => {
    fetchFiles();
    showSnackbar('Файл успешно загружен и обработан', 'success');
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleOpenAnalysisDialog = (fileId) => {
    setSelectedFileId(fileId);
    setAnalysisDialogOpen(true);
  };

  const handleCloseAnalysisDialog = () => {
    setAnalysisDialogOpen(false);
  };

  const handleAnalysisTypeChange = (event) => {
    setAnalysisType(event.target.value);
  };

  const handleAnalyzeData = async () => {
    if (!selectedFileId) {
      showSnackbar('Выберите файл для анализа', 'error');
      return;
    }

    setAnalyzing(true);
    try {
      const response = await api.post(`/analytics/analyze`, {
        file_id: selectedFileId,
        analysis_type: analysisType,
        parameters: {}
      });
      
      showSnackbar('Анализ данных успешно выполнен', 'success');
      setTabValue(1); // Переключаемся на вкладку с аналитикой
      setAnalysisDialogOpen(false);
    } catch (error) {
      console.error('Error analyzing data:', error);
      showSnackbar('Ошибка при анализе данных: ' + (error.response?.data?.detail || 'Неизвестная ошибка'), 'error');
    } finally {
      setAnalyzing(false);
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

  if (!cabinet) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        Кабинет не найден
      </Alert>
    );
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        {cabinet.name}
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Маркетплейс: {cabinet.marketplace === 'ozon' ? 'Ozon' : 'Wildberries'}
      </Typography>
      
      <Divider sx={{ my: 2 }} />
      
      <Box sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Файлы" />
          <Tab label="Аналитика" />
        </Tabs>
      </Box>
      
      {tabValue === 0 && (
        <>
          <FileUpload cabinetId={cabinetId} onUploadSuccess={handleUploadSuccess} />
          <FilesList 
            files={files} 
            onRefresh={fetchFiles} 
            onAnalyzeFile={handleOpenAnalysisDialog}
          />
        </>
      )}
      
      {tabValue === 1 && selectedFileId && (
      <AnalyticsDisplay
        fileId={selectedFileId}
        analysisType={analysisType}
      />
    )}

      {/* Диалог выбора типа анализа */}
      <Dialog open={analysisDialogOpen} onClose={handleCloseAnalysisDialog}>
        <DialogTitle>Анализ данных</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Выберите тип анализа для выбранного файла:
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="analysis-type-label">Тип анализа</InputLabel>
            <Select
              labelId="analysis-type-label"
              value={analysisType}
              label="Тип анализа"
              onChange={handleAnalysisTypeChange}
            >
              <MenuItem value="trends">Анализ трендов</MenuItem>
              <MenuItem value="competitors">Анализ конкурентов</MenuItem>
              <MenuItem value="metrics">Анализ метрик и генерация отчета</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAnalysisDialog}>Отмена</Button>
          <Button 
            onClick={handleAnalyzeData} 
            variant="contained" 
            disabled={analyzing}
          >
            {analyzing ? <CircularProgress size={24} /> : 'Анализировать'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CabinetDetail;
