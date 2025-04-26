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
  Chip
} from '@mui/material';
import { useSnackbar } from '../../contexts/SnackbarContext';
import api from '../../services/api';

const TasksList = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { showSnackbar } = useSnackbar();

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/tasks');
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError('Ошибка при загрузке задач');
      showSnackbar('Ошибка при загрузке задач', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await api.put(`/tasks/${taskId}/complete`);
      showSnackbar('Задача отмечена как выполненная', 'success');
      fetchTasks(); // Обновляем список задач
    } catch (error) {
      console.error('Error completing task:', error);
      showSnackbar('Ошибка при обновлении статуса задачи', 'error');
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту задачу?')) {
      return;
    }
    
    try {
      await api.delete(`/tasks/${taskId}`);
      showSnackbar('Задача успешно удалена', 'success');
      fetchTasks(); // Обновляем список задач
    } catch (error) {
      console.error('Error deleting task:', error);
      showSnackbar('Ошибка при удалении задачи', 'error');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'in_progress':
        return 'info';
      case 'completed':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending':
        return 'Ожидает';
      case 'in_progress':
        return 'В процессе';
      case 'completed':
        return 'Выполнена';
      default:
        return 'Неизвестно';
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
        Задачи
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {tasks.length > 0 ? (
          tasks.map((task) => (
            <Grid item xs={12} key={task.id}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="h6">
                      {task.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      Проект: {task.project_name} | 
                      Создана: {new Date(task.created_at).toLocaleString()} | 
                      Статус: <Chip 
                        label={getStatusText(task.status)} 
                        color={getStatusColor(task.status)} 
                        size="small" 
                      />
                    </Typography>
                    <Typography variant="body1">
                      {task.description}
                    </Typography>
                  </Box>
                  <Box>
                    {task.status !== 'completed' && (
                      <Button 
                        variant="outlined" 
                        color="success"
                        onClick={() => handleCompleteTask(task.id)}
                        sx={{ mr: 1 }}
                      >
                        Выполнить
                      </Button>
                    )}
                    <Button 
                      variant="outlined" 
                      color="error"
                      onClick={() => handleDeleteTask(task.id)}
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
              У вас пока нет задач. Задачи создаются автоматически на основе анализа данных или могут быть добавлены вручную.
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default TasksList;
