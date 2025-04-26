import React from 'react';
import { Box, Tab, Tabs, Typography } from '@mui/material';
import AnalyticsRunner from '../components/analytics/AnalyticsRunner';

/**
 * Компонент страницы аналитики для отображения и запуска анализа данных
 * 
 * @param {Object} props - Свойства компонента
 * @param {number} props.fileId - ID файла для анализа
 * @param {string} props.marketplace - Название маркетплейса
 */
const AnalyticsPage = ({ fileId, marketplace }) => {
  const [tabValue, setTabValue] = React.useState(0);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Типы анализа, соответствующие вкладкам
  const analysisTypes = ['trends', 'competitors', 'metrics'];

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" gutterBottom>
        Аналитика данных
      </Typography>
      
      <Typography variant="subtitle1" gutterBottom>
        Маркетплейс: {marketplace || 'Не указан'}
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="analytics tabs"
        >
          <Tab label="Анализ трендов" />
          <Tab label="Анализ конкурентов" />
          <Tab label="Метрики" />
        </Tabs>
      </Box>
      
      {/* Содержимое вкладок */}
      <TabPanel value={tabValue} index={0}>
        <AnalyticsRunner fileId={fileId} analysisType={analysisTypes[0]} />
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        <AnalyticsRunner fileId={fileId} analysisType={analysisTypes[1]} />
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        <AnalyticsRunner fileId={fileId} analysisType={analysisTypes[2]} />
      </TabPanel>
    </Box>
  );
};

// Вспомогательный компонент для содержимого вкладок
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default AnalyticsPage;
