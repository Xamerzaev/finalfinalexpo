import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  Paper, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  CircularProgress,
  Alert
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { styled } from '@mui/material/styles';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';

// Стилизованный компонент для загрузки файлов
const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const FileUpload = ({ cabinetId, onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileType, setFileType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Проверка расширения файла
      const fileExtension = file.name.split('.').pop().toLowerCase();
      if (['xlsx', 'xls', 'csv'].includes(fileExtension)) {
        setSelectedFile(file);
        setError('');
      } else {
        setSelectedFile(null);
        setError('Неподдерживаемый формат файла. Пожалуйста, загрузите файл Excel (.xlsx, .xls) или CSV (.csv)');
      }
    }
  };

  const handleFileTypeChange = (event) => {
    setFileType(event.target.value);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Пожалуйста, выберите файл для загрузки');
      return;
    }

    if (!fileType) {
      setError('Пожалуйста, выберите тип файла');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('cabinet_id', cabinetId);
      formData.append('file_type', fileType);

      const response = await api.post('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      showSnackbar('Файл успешно загружен', 'success');
      setSelectedFile(null);
      setFileType('');
      
      // Вызываем колбэк для обновления родительского компонента
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setError(
        error.response?.data?.detail || 
        'Произошла ошибка при загрузке файла. Пожалуйста, попробуйте еще раз.'
      );
      showSnackbar('Ошибка при загрузке файла', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Загрузка файла
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <FormControl fullWidth required>
          <InputLabel id="file-type-label">Тип файла</InputLabel>
          <Select
            labelId="file-type-label"
            value={fileType}
            label="Тип файла"
            onChange={handleFileTypeChange}
            disabled={loading}
          >
            <MenuItem value="metrics">Метрики</MenuItem>
            <MenuItem value="report_table">Отчетная таблица</MenuItem>
          </Select>
        </FormControl>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            component="label"
            variant="contained"
            startIcon={<CloudUploadIcon />}
            disabled={loading}
          >
            Выбрать файл
            <VisuallyHiddenInput type="file" onChange={handleFileChange} />
          </Button>
          
          {selectedFile && (
            <Typography variant="body2" color="text.secondary">
              {selectedFile.name}
            </Typography>
          )}
        </Box>
        
        <Button
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={!selectedFile || !fileType || loading}
          sx={{ mt: 1 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Загрузить'}
        </Button>
      </Box>
    </Paper>
  );
};

export default FileUpload;
