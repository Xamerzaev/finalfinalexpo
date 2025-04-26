import React from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { SnackbarProvider } from './contexts/SnackbarContext';

// Components
import Layout from './components/layout/Layout';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/dashboard/Dashboard';
import ProjectsList from './components/projects/ProjectsList';
import ProjectDetail from './components/projects/ProjectDetail';
import CabinetDetail from './components/cabinets/CabinetDetail';
import ReportDetail from './components/reports/ReportDetail';
import ReportsList from './components/reports/ReportsList';
import TasksList from './components/tasks/TasksList';
import PrivateRoute from './components/auth/PrivateRoute';
import Settings from './components/settings/Settings';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      'Roboto',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider>
        <AuthProvider>
          <Router>
            <Switch>
              <Route path="/login" component={Login} />
              <Route path="/register" component={Register} />
              <PrivateRoute path="/">
                <Layout>
                  <Switch>
                    <PrivateRoute exact path="/" component={Dashboard} />
                    <PrivateRoute exact path="/projects" component={ProjectsList} />
                    <PrivateRoute path="/projects/:projectId" component={ProjectDetail} />
                    <PrivateRoute path="/cabinets/:cabinetId" component={CabinetDetail} />
                    <PrivateRoute exact path="/reports" component={ReportsList} />
                    <PrivateRoute path="/reports/:reportId" component={ReportDetail} />
                    <PrivateRoute path="/tasks" component={TasksList} />
                    <PrivateRoute path="/settings" component={Settings} />
                    <Redirect to="/" />
                  </Switch>
                </Layout>
              </PrivateRoute>
            </Switch>
          </Router>
        </AuthProvider>
      </SnackbarProvider>
    </ThemeProvider>
  );
}

export default App;
