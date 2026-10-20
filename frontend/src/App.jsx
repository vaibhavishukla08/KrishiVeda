// App.jsx
import { useEffect } from 'react';
import AppRoutes from './routes/AppRoutes';
import useAuthStore from './hooks/useAuthStore';

const App = () => {
  const restoreSession = useAuthStore((s) => s.restoreSession);

  // Restore session on every app load
  useEffect(() => {
    restoreSession();
  }, [restoreSession]);

  return <AppRoutes />;
};

export default App;