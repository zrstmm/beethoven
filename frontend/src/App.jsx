import { Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import { isAuthenticated } from './api/client'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import AnalysesPage from './pages/AnalysesPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'

function PrivateRoute({ children, city, setCity }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />
  }
  return <Layout city={city} setCity={setCity}>{children}</Layout>
}

export default function App() {
  const [city, setCity] = useState(() => localStorage.getItem('beethoven_city') || 'astana')

  const handleSetCity = (c) => {
    setCity(c)
    localStorage.setItem('beethoven_city', c)
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute city={city} setCity={handleSetCity}>
            <AnalysesPage city={city} />
          </PrivateRoute>
        }
      />
      <Route
        path="/analytics"
        element={
          <PrivateRoute city={city} setCity={handleSetCity}>
            <AnalyticsPage city={city} />
          </PrivateRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <PrivateRoute city={city} setCity={handleSetCity}>
            <SettingsPage />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}
