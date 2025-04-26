import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  TextField, 
  Button, 
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';
import { useHistory } from 'react-router-dom';

const ProjectForm = ({ project = null, onSuccess }) => {
  const [name, setName] = useState(project?.name || '');
  const [description, setDescription] = useState(project?.description || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();
  const history = useHistory();
  const isEditing = !!project;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Название проекта обязательно');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      let response;
      
      if (isEditing) {
        response = await api.put(`/projects/${project.id}`, {
          name,
          description
        });
        showSnackbar('Проект успешно обновлен', 'success');
      } else {
        response = await api.post('/projects', {
          name,
          description
        });
        showSnackbar('Проект успешно создан', 'success');
      }
      
      if (onSuccess) {
        onSuccess(response.data);
      } else {
        history.push(`/projects/${response.data.id}`);
      }
    } catch (error) {
      console.error('Error saving project:', error);
      setError(
        error.response?.data?.detail || 
        'Произошла ошибка при сохранении проекта. Пожалуйста, попробуйте еще раз.'
      );
      showSnackbar('Ошибка при сохранении проекта', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {isEditing ? 'Редактирование проекта' : 'Новый проект'}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <form onSubmit={handleSubmit}>
        <TextField
          label="Название проекта"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          required
          margin="normal"
          disabled={loading}
        />
        
        <TextField
          label="Описание"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          fullWidth
          multiline
          rows={3}
          margin="normal"
          disabled={loading}
        />
        
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            type="button"
            variant="outlined"
            onClick={() => history.goBack()}
            sx={{ mr: 1 }}
            disabled={loading}
          >
            Отмена
          </Button>
          
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : (isEditing ? 'Сохранить' : 'Создать')}
          </Button>
        </Box>
      </form>
    </Paper>
  );
};

const CabinetForm = ({ projectId, cabinet = null, onSuccess }) => {
  const [name, setName] = useState(cabinet?.name || '');
  const [marketplace, setMarketplace] = useState(cabinet?.marketplace || 'ozon');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();
  const history = useHistory();
  const isEditing = !!cabinet;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Название кабинета обязательно');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      let response;
      
      if (isEditing) {
        response = await api.put(`/cabinets/${cabinet.id}`, {
          name,
          marketplace
        });
        showSnackbar('Кабинет успешно обновлен', 'success');
      } else {
        response = await api.post('/cabinets', {
          name,
          marketplace,
          project_id: projectId
        });
        showSnackbar('Кабинет успешно создан', 'success');
      }
      
      if (onSuccess) {
        onSuccess(response.data);
      } else {
        history.push(`/cabinets/${response.data.id}`);
      }
    } catch (error) {
      console.error('Error saving cabinet:', error);
      setError(
        error.response?.data?.detail || 
        'Произошла ошибка при сохранении кабинета. Пожалуйста, попробуйте еще раз.'
      );
      showSnackbar('Ошибка при сохранении кабинета', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {isEditing ? 'Редактирование кабинета' : 'Новый кабинет'}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <form onSubmit={handleSubmit}>
        <TextField
          label="Название кабинета"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          required
          margin="normal"
          disabled={loading}
        />
        
        <FormControl fullWidth margin="normal" disabled={loading}>
          <InputLabel id="marketplace-label">Маркетплейс</InputLabel>
          <Select
            labelId="marketplace-label"
            value={marketplace}
            label="Маркетплейс"
            onChange={(e) => setMarketplace(e.target.value)}
          >
            <MenuItem value="ozon">Ozon</MenuItem>
            <MenuItem value="wildberries">Wildberries</MenuItem>
          </Select>
        </FormControl>
        
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            type="button"
            variant="outlined"
            onClick={() => history.goBack()}
            sx={{ mr: 1 }}
            disabled={loading}
          >
            Отмена
          </Button>
          
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : (isEditing ? 'Сохранить' : 'Создать')}
          </Button>
        </Box>
      </form>
    </Paper>
  );
};

const ProjectDetail = ({ match }) => {
  const projectId = match.params.projectId;
  const [project, setProject] = useState(null);
  const [cabinets, setCabinets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showNewCabinetForm, setShowNewCabinetForm] = useState(false);
  const { showSnackbar } = useSnackbar();
  const history = useHistory();
  const isNewProject = projectId === 'new';

  const fetchProjectData = async () => {
    if (isNewProject) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const [projectResponse, cabinetsResponse] = await Promise.all([
        api.get(`/projects/${projectId}`),
        api.get(`/cabinets?project_id=${projectId}`)
      ]);
      
      setProject(projectResponse.data);
      setCabinets(cabinetsResponse.data);
    } catch (error) {
      console.error('Error fetching project data:', error);
      setError('Ошибка при загрузке данных проекта');
      showSnackbar('Ошибка при загрузке данных', 'error');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const handleProjectSuccess = (updatedProject) => {
    setProject(updatedProject);
    if (isNewProject) {
      history.replace(`/projects/${updatedProject.id}`);
    }
  };

  const handleCabinetSuccess = (newCabinet) => {
    setCabinets([...cabinets, newCabinet]);
    setShowNewCabinetForm(false);
  };

  const handleDeleteProject = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить этот проект? Это действие нельзя отменить.')) {
      return;
    }
    
    try {
      await api.delete(`/projects/${projectId}`);
      showSnackbar('Проект успешно удален', 'success');
      history.push('/projects');
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

  if (error && !isNewProject) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (isNewProject) {
    return <ProjectForm onSuccess={handleProjectSuccess} />;
  }

  if (!project) {
    return (
      <Alert severity="warning" sx={{ mb: 2 }}>
        Проект не найден
      </Alert>
    );
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          {project.name}
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            color="primary"
            onClick={() => setProject({ ...project, isEditing: true })}
            sx={{ mr: 1 }}
          >
            Редактировать
          </Button>
          <Button 
            variant="outlined" 
            color="error"
            onClick={handleDeleteProject}
          >
            Удалить
          </Button>
        </Box>
      </Box>
      
      {project.description && (
        <Typography variant="body1" paragraph>
          {project.description}
        </Typography>
      )}
      
      {project.isEditing ? (
        <ProjectForm 
          project={project} 
          onSuccess={(updatedProject) => {
            setProject(updatedProject);
            showSnackbar('Проект успешно обновлен', 'success');
          }} 
        />
      ) : (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, mt: 4 }}>
            <Typography variant="h5">
              Кабинеты маркетплейсов
            </Typography>
            <Button 
              variant="contained" 
              color="primary"
              onClick={() => setShowNewCabinetForm(true)}
            >
              Добавить кабинет
            </Button>
          </Box>
          
          {showNewCabinetForm && (
            <CabinetForm 
              projectId={projectId} 
              onSuccess={handleCabinetSuccess} 
            />
          )}
          
          <Grid container spacing={3}>
            {cabinets.length > 0 ? (
              cabinets.map((cabinet) => (
                <Grid item xs={12} sm={6} md={4} key={cabinet.id}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6">
                      {cabinet.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Маркетплейс: {cabinet.marketplace === 'ozon' ? 'Ozon' : 'Wildberries'}
                    </Typography>
                    <Button 
                      variant="outlined" 
                      size="small"
                      onClick={() => history.push(`/cabinets/${cabinet.id}`)}
                    >
                      Открыть
                    </Button>
                  </Paper>
                </Grid>
              ))
            ) : (
              <Grid item xs={12}>
                <Alert severity="info">
                  В этом проекте пока нет кабинетов. Добавьте кабинет, чтобы начать работу с данными маркетплейса.
                </Alert>
              </Grid>
            )}
          </Grid>
        </>
      )}
    </Box>
  );
};

export default ProjectDetail;
