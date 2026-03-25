import axios from 'axios';

const API_URL = 'http://localhost:5000/api/auth';

const authService = {
  register: async (userData: any) => {
    const response = await axios.post(`${API_URL}/register`, userData);
    return response.data;
  },

  login: async (userData: any) => {
    const response = await axios.post(`${API_URL}/login`, userData);
    if (response.data.token) {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('user');
  },

  getCurrentUser: () => {
    return JSON.parse(localStorage.getItem('user') || 'null');
  },
  
  isAuthenticated: () => {
    return !!localStorage.getItem('user');
  }
};

export default authService;
