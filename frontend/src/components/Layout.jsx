import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken } from '../api/client'
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
          <select
            className="city-select"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          >
            {Object.entries(CITIES).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button className="logout-btn" onClick={handleLogout}>Выйти</button>
        </div>
      </header>
      <div className="main-container">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'} end>
              Анализы
            </NavLink>
            <NavLink to="/analytics" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              Аналитика
            </NavLink>
            <NavLink to="/settings" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
              Настройки
            </NavLink>
          </nav>
        </aside>
        <main className="content">
          {children}
        </main>
      </div>
    </div>
  )
}
