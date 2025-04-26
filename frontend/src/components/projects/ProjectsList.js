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
  Card,
  CardContent,
  CardActions
} from '@mui/material';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';
import { Link, useHistory } from 'react-router-dom';

const ProjectsList = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();
  const history = useHistory();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/projects');
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError('Ошибка при загрузке проектов');
      showSnackbar('Ошибка при загрузке проектов', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот проект? Это действие нельзя отменить.')) {
      return;
    }
    
    try {
      await api.delete(`/projects/${projectId}`);
      showSnackbar('Проект успешно удален', 'success');
      fetchProjects(); // Обновляем список проектов
    } catch (error) {
      console.error('Error deleting project:', error);
      showSnackbar('Ошибка при удалении проекта', 'error');
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Проекты
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => history.push('/projects/new')}
        >
          Создать проект
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
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
                  <Button 
                    size="small" 
                    color="error"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    Удалить
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
  );
};

export default ProjectsList;
