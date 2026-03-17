import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';
import { useAuth } from './auth';

const ClientContext = createContext();

export const useClients = () => {
  const context = useContext(ClientContext);
  if (!context) {
    throw new Error('useClients must be used within a ClientProvider');
  }
  return context;
};

export const ClientProvider = ({ children }) => {
  const { isAuthenticated, user } = useAuth();
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchClients = async () => {
    if (!isAuthenticated || (user?.role !== 'hr' && user?.role !== 'admin')) {
      setClients([]);
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const response = await api.get('/api/hr/clients');
      setClients(response.data);
    } catch (error) {
      console.error('Error fetching clients:', error);
      setClients([]);
    } finally {
      setLoading(false);
    }
  };

  const addClient = (client) => {
    setClients(prevClients => [client, ...prevClients]);
  };

  const removeClient = (clientId) => {
    setClients(prevClients => prevClients.filter(client => client.id !== clientId));
  };

  useEffect(() => {
    fetchClients();
  }, [isAuthenticated, user]);

  const value = {
    clients,
    loading,
    fetchClients,
    addClient,
    removeClient
  };

  return (
    <ClientContext.Provider value={value}>
      {children}
    </ClientContext.Provider>
  );
};
