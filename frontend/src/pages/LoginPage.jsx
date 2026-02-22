import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/client'
import './LoginPage.css'

export default function LoginPage() {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(password)
      navigate('/')
    } catch {
      setError('Неверный пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form className="login-form" onSubmit={handleSubmit}>
        <h1 className="login-logo">BEETHOVEN</h1>
        <p className="login-subtitle">Панель управления</p>
        <input
          type="password"
          className="login-input"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoFocus
        />
        {error && <p className="login-error">{error}</p>}
        <button className="login-btn" type="submit" disabled={loading}>
          {loading ? 'Вход...' : 'Войти'}
        </button>
      </form>
    </div>
  )
}
