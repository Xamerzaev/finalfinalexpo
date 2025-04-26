import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardActions,
  Divider
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [cabinets, setCabinets] = useState([]);
  const [recentReports, setRecentReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      // Загружаем данные параллельно
      const [projectsResponse, cabinetsResponse, reportsResponse] = await Promise.all([
        api.get('/projects'),
        api.get('/cabinets'),
        api.get('/reports?limit=5')
      ]);
      
      setProjects(projectsResponse.data);
      setCabinets(cabinetsResponse.data);
      setRecentReports(reportsResponse.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Ошибка при загрузке данных дашборда');
      showSnackbar('Ошибка при загрузке данных', 'error');
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

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Дашборд
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* Проекты */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">
            Проекты
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
            component={Link}
            to="/projects/new"
          >
            Новый проект
          </Button>
        </Box>
        
        <Grid container spacing={3}>
          {projects.length > 0 ? (
            projects.map((project) => (
              <Grid item xs={12} sm={6} md={4} key={project.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" component="div">
                      {project.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {project.description || 'Нет описания'}
                    </Typography>
                    <Typography variant="body2">
                      Кабинетов: {project.cabinets?.length || 0}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      component={Link} 
                      to={`/projects/${project.id}`}
                    >
                      Открыть
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Alert severity="info">
                У вас пока нет проектов. Создайте новый проект, чтобы начать работу.
              </Alert>
            </Grid>
          )}
        </Grid>
      </Box>
      
      <Divider sx={{ my: 3 }} />
      
      {/* Кабинеты */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Кабинеты маркетплейсов
        </Typography>
        
        <Grid container spacing={3}>
          {cabinets.length > 0 ? (
            cabinets.map((cabinet) => (
              <Grid item xs={12} sm={6} md={4} key={cabinet.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" component="div">
                      {cabinet.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Маркетплейс: {cabinet.marketplace === 'ozon' ? 'Ozon' : 'Wildberries'}
                    </Typography>
                    <Typography variant="body2">
                      Проект: {cabinet.project_name || 'Не указан'}
                    </Typography>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      component={Link} 
                      to={`/cabinets/${cabinet.id}`}
                    >
                      Открыть
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Alert severity="info">
                У вас пока нет кабинетов маркетплейсов. Создайте новый кабинет в проекте.
              </Alert>
            </Grid>
          )}
        </Grid>
      </Box>
      
      <Divider sx={{ my: 3 }} />
      
      {/* Последние отчеты */}
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">
            Последние отчеты
          </Typography>
          <Button 
            variant="outlined" 
            component={Link}
            to="/reports"
          >
            Все отчеты
          </Button>
        </Box>
        
        <Grid container spacing={3}>
          {recentReports.length > 0 ? (
            recentReports.map((report) => (
              <Grid item xs={12} key={report.id}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6">
                    {report.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Кабинет: {report.cabinet_name} | 
                    Период: {new Date(report.period_start).toLocaleDateString()} - {new Date(report.period_end).toLocaleDateString()} | 
                    Создан: {new Date(report.created_at).toLocaleString()}
                  </Typography>
                  <Button 
                    size="small" 
                    component={Link} 
                    to={`/reports/${report.id}`}
                  >
                    Просмотреть
                  </Button>
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
    </Box>
  );
};

export default Dashboard;
