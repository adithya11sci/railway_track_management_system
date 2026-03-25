import { Navigate, Outlet } from 'react-router-dom';
import authService from '../services/auth';

const ProtectedRoute = () => {
    const isAuth = authService.isAuthenticated();
    return isAuth ? <Outlet /> : <Navigate to="/register" replace />;
};

export default ProtectedRoute;
