import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken } from '../api/client'
import { BarChart3, PieChart, Settings, LogOut } from 'lucide-react'
import './Layout.css'

const CITIES = {
  astana: 'Астана',
  ust_kamenogorsk: 'Усть-Каменогорск',
}

export default function Layout({ children, city, setCity }) {
  const navigate = useNavigate()

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="layout">
      <header className="header">
        <div className="header-left">
          <h1 className="logo">BEETHOVEN</h1>
        </div>
        <div className="header-right">
          <div className="city-segmented">
            {Object.entries(CITIES).map(([value, label]) => (
              <button
                key={value}
                className={`city-seg-btn ${city === value ? 'active' : ''}`}
                onClick={() => setCity(value)}
              >
                {label}
              </button>
            ))}
          </div>
          <button className="logout-btn" onClick={handleLogout}>
            <LogOut size={16} />
          </button>
        </div>
      </header>
      <div className="main-container">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'} end>
              <BarChart3 size={18} />
              <span>Анализы</span>
            </NavLink>
            <NavLink to="/analytics" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <PieChart size={18} />
              <span>Аналитика</span>
            </NavLink>
            <NavLink to="/settings" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              <Settings size={18} />
              <span>Настройки</span>
            </NavLink>
          </nav>
          <button className="sidebar-logout" onClick={handleLogout}>
            <LogOut size={16} />
            <span>Выйти</span>
          </button>
        </aside>
        <main className="content">
          {children}
        </main>
      </div>
    </div>
  )
}
