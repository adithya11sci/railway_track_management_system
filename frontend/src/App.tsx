import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TrainDelay from './pages/TrainDelay'
import PassengerQuery from './pages/PassengerQuery'
import Alerts from './pages/Alerts'
import Agents from './pages/Agents'
import Timetable from './pages/Timetable'
import TrainDetails from './pages/TrainDetails'
import Register from './pages/Register'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import authService from './services/auth'

function App() {
  const isAuth = authService.isAuthenticated();

  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        {/* Auth Routes */}
        <Route path="/register" element={!isAuth ? <Register /> : <Navigate to="/" />} />
        <Route path="/login" element={!isAuth ? <Login /> : <Navigate to="/" />} />

        {/* Protected Dashboard Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="train-delay" element={<TrainDelay />} />
            <Route path="passenger-query" element={<PassengerQuery />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="agents" element={<Agents />} />
            <Route path="timetable" element={<Timetable />} />
            <Route path="train/:id" element={<TrainDetails />} />
          </Route>
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to={isAuth ? "/" : "/register"} />} />
      </Routes>
    </Router>
  )
}

export default App
