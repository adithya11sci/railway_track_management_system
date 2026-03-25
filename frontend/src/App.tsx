import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TrainDelay from './pages/TrainDelay'
import PassengerQuery from './pages/PassengerQuery'
import Alerts from './pages/Alerts'
import Agents from './pages/Agents'
import Timetable from './pages/Timetable'
import TrainDetails from './pages/TrainDetails'

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="train-delay" element={<TrainDelay />} />
          <Route path="passenger-query" element={<PassengerQuery />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="agents" element={<Agents />} />
          <Route path="timetable" element={<Timetable />} />
          <Route path="train/:id" element={<TrainDetails />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
