import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Container, Typography, Tabs, Tab, Paper, Button } from '@mui/material';
import api from '../services/api';
import AnalyticsRunner from '../components/analytics/AnalyticsRunner';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const FileDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    const fetchFile = async () => {
      try {
        const response = await api.get(`/files/${id}`);
        setFile(response.data);
      } catch (err) {
        console.error('Error fetching file:', err);
        setError('Не удалось загрузить данные файла');
      } finally {
        setLoading(false);
      }
    };

    fetchFile();
  }, [id]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <Container>
        <Typography>Загрузка...</Typography>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Typography color="error">{error}</Typography>
        <Button variant="contained" onClick={() => navigate(-1)}>
          Назад
        </Button>
      </Container>
    );
  }

  if (!file) {
    return (
      <Container>
        <Typography>Файл не найден</Typography>
        <Button variant="contained" onClick={() => navigate(-1)}>
          Назад
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {file.filename}
        </Typography>
        <Typography variant="body1" gutterBottom>
          Маркетплейс: {file.cabinet?.marketplace || 'Не указан'}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Загружен: {new Date(file.created_at).toLocaleString()}
        </Typography>
      </Paper>

      <Box sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="file tabs">
            <Tab label="ФАЙЛЫ" />
            <Tab label="АНАЛИТИКА" />
          </Tabs>
        </Box>
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Содержимое файла
          </Typography>
          {/* Здесь можно отобразить содержимое файла или другую информацию */}
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <AnalyticsRunner 
            fileId={parseInt(id)} 
            analysisType="trends" 
          />
        </TabPanel>
      </Box>
    </Container>
  );
};

export default FileDetailPage;
