import { useState, useEffect } from 'react'
import { getSettings, updateSetting } from '../api/client'
import { Settings } from 'lucide-react'
import './SettingsPage.css'

const SETTING_LABELS = {
  prompt_teacher: 'Промпт для преподавателей',
  prompt_sales: 'Промпт для менеджеров отдела продаж',
  admin_password: 'Пароль админ-панели',
}

export default function SettingsPage() {
  const [settings, setSettings] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState({})
  const [edited, setEdited] = useState({})

  useEffect(() => {
    async function load() {
      try {
        const data = await getSettings()
        setSettings(data)
        const initial = {}
        data.forEach(s => { initial[s.key] = s.value })
        setEdited(initial)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleSave(key) {
    setSaving(s => ({ ...s, [key]: true }))
    try {
      await updateSetting(key, edited[key])
      setSettings(prev =>
        prev.map(s => s.key === key ? { ...s, value: edited[key] } : s)
      )
    } catch (err) {
      console.error(err)
      alert('Ошибка сохранения')
    } finally {
      setSaving(s => ({ ...s, [key]: false }))
    }
  }

  if (loading) return <p className="settings-loading">Загрузка...</p>

  return (
    <div className="settings-page">
      <div className="settings-header">
        <Settings size={20} />
        <h2 className="settings-title">Настройки</h2>
      </div>
      {settings.map(setting => {
        const isPassword = setting.key === 'admin_password'
        const hasChanges = edited[setting.key] !== setting.value
        return (
          <div key={setting.key} className="setting-card">
            <label className="setting-label">
              {SETTING_LABELS[setting.key] || setting.key}
            </label>
            {isPassword ? (
              <input
                type="text"
                className="setting-input"
                value={edited[setting.key] || ''}
                onChange={e => setEdited(prev => ({ ...prev, [setting.key]: e.target.value }))}
              />
            ) : (
              <textarea
                className="setting-textarea"
                rows={12}
                value={edited[setting.key] || ''}
                onChange={e => setEdited(prev => ({ ...prev, [setting.key]: e.target.value }))}
              />
            )}
            <button
              className="setting-save"
              onClick={() => handleSave(setting.key)}
              disabled={!hasChanges || saving[setting.key]}
            >
              {saving[setting.key] ? 'Сохранение...' : 'Сохранить'}
            </button>
          </div>
        )
      })}
    </div>
  )
}
