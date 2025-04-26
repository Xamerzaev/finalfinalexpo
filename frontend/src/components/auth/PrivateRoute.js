import React from 'react';
import { Route, Redirect } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CircularProgress, Box } from '@mui/material';

const PrivateRoute = ({ component: Component, ...rest }) => {
  const { isAuthenticated, currentUser } = useAuth();

  return (
    <Route
      {...rest}
      render={(props) => {
        if (isAuthenticated === null) {
          // Если статус аутентификации еще не определен, показываем индикатор загрузки
          return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
              <CircularProgress />
            </Box>
          );
        }

        return isAuthenticated ? (
          <Component {...props} />
        ) : (
          <Redirect to={{ pathname: '/login', state: { from: props.location } }} />
        );
      }}
    />
  );
};

export default PrivateRoute;
