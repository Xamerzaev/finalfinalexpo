import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  TextField, 
  Button, 
  CircularProgress,
  Alert,
  Link as MuiLink
} from '@mui/material';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useSnackbar } from '../../contexts/SnackbarContext';

const Login = ({ history }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const { showSnackbar } = useSnackbar();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      setError('Пожалуйста, введите имя пользователя и пароль');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      await login(username, password);
      showSnackbar('Вход выполнен успешно', 'success');
      history.push('/');
    } catch (error) {
      console.error('Login error:', error);
      setError(
        error.response?.data?.detail || 
        'Ошибка при входе. Пожалуйста, проверьте имя пользователя и пароль.'
      );
      showSnackbar('Ошибка при входе', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        bgcolor: 'background.default',
        p: 2
      }}
    >
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          maxWidth: 400, 
          width: '100%',
          borderRadius: 2
        }}
      >
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          AI Analytics Assistant
        </Typography>
        
        <Typography variant="subtitle1" align="center" color="text.secondary" sx={{ mb: 3 }}>
          Войдите в систему для доступа к аналитике
        </Typography>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <TextField
            label="Имя пользователя"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            fullWidth
            margin="normal"
            required
            disabled={loading}
          />
          
          <TextField
            label="Пароль"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            margin="normal"
            required
            disabled={loading}
          />
          
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Войти'}
          </Button>
        </form>
        
        <Typography variant="body2" align="center">
          Нет аккаунта?{' '}
          <MuiLink component={Link} to="/register">
            Зарегистрироваться
          </MuiLink>
        </Typography>
        
        <Typography variant="caption" align="center" display="block" sx={{ mt: 3 }}>
          Для демо-доступа используйте:<br />
          Имя пользователя: admin<br />
          Пароль: admin
        </Typography>
      </Paper>
    </Box>
  );
};

export default Login;
