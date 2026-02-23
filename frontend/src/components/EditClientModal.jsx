import { useState, useEffect } from 'react'
import { updateClient } from '../api/client'
import { X } from 'lucide-react'
import './EditClientModal.css'

const RESULT_OPTIONS = [
  { value: '', label: 'Не указан' },
  { value: 'bought', label: 'Купил' },
  { value: 'not_bought', label: 'Не купил' },
  { value: 'prepayment', label: 'Предоплата' },
]

export default function EditClientModal({ client, onClose, onSaved }) {
  const [name, setName] = useState(client.name || '')
  const [result, setResult] = useState(client.result || '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    document.body.classList.add('modal-open')
    return () => document.body.classList.remove('modal-open')
  }, [])

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) onClose()
  }

  async function handleSave(e) {
    e.preventDefault()
    setSaving(true)
    setError('')

    const data = {}
    if (name !== client.name) data.name = name
    if (result !== (client.result || '')) data.result = result || null

    if (Object.keys(data).length === 0) {
      onClose()
      return
    }

    try {
      await updateClient(client.id, data)
      onSaved()
    } catch (err) {
      setError('Ошибка сохранения')
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="edit-overlay" onClick={handleOverlayClick}>
      <div className="edit-modal">
        <button className="edit-close" onClick={onClose}><X size={18} /></button>
        <h3 className="edit-title">Редактировать клиента</h3>
        <form onSubmit={handleSave}>
          <label className="edit-label">
            Имя клиента
            <input
              className="edit-input"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </label>
          <label className="edit-label">
            Результат
            <select
              className="edit-select"
              value={result}
              onChange={(e) => setResult(e.target.value)}
            >
              {RESULT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
          {error && <p className="edit-error">{error}</p>}
          <button className="edit-save" type="submit" disabled={saving}>
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </form>
      </div>
    </div>
  )
}
