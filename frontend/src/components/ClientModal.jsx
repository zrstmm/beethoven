import { useState, useEffect } from 'react'
import { getClientDetail } from '../api/client'
import './ClientModal.css'

const RESULT_LABELS = {
  bought: 'Купил',
  not_bought: 'Не купил',
  prepayment: 'Предоплата',
}

const RESULT_COLORS = {
  bought: 'var(--green)',
  not_bought: 'var(--red)',
  prepayment: 'var(--yellow)',
}

const ROLE_LABELS = {
  teacher: 'Преподаватель',
  sales_manager: 'Менеджер отдела продаж',
}

const DIR_LABELS = {
  guitar: 'Гитара',
  piano: 'Фортепиано',
  vocal: 'Вокал',
  dombra: 'Домбра',
}

function ScoreBar({ score }) {
  const pct = (score / 10) * 100
  const color = score >= 7 ? 'var(--green)' : score >= 4 ? 'var(--yellow)' : 'var(--red)'
  return (
    <div className="score-bar-wrap">
      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="score-value" style={{ color }}>{score}/10</span>
    </div>
  )
}

export default function ClientModal({ clientId, onClose }) {
  const [client, setClient] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await getClientDetail(clientId)
        setClient(data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [clientId])

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) onClose()
  }

  if (loading) {
    return (
      <div className="modal-overlay" onClick={handleOverlayClick}>
        <div className="modal">
          <p className="modal-loading">Загрузка...</p>
        </div>
      </div>
    )
  }

  if (!client) return null

  const dt = new Date(client.lesson_datetime)
  const dateStr = dt.toLocaleDateString('ru', {
    day: '2-digit', month: 'long', year: 'numeric'
  })
  const timeStr = dt.toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal">
        <button className="modal-close" onClick={onClose}>✕</button>

        <div className="modal-header">
          <h2 className="modal-title">{client.name}</h2>
          <p className="modal-meta">{dateStr}, {timeStr}</p>
          {client.result && (
            <span className="modal-result" style={{ color: RESULT_COLORS[client.result] }}>
              {RESULT_LABELS[client.result]}
            </span>
          )}
        </div>

        {client.recordings.length === 0 && (
          <p className="modal-empty">Записи ещё не загружены</p>
        )}

        {client.recordings.map(rec => (
          <RecordingBlock key={rec.id} recording={rec} />
        ))}
      </div>
    </div>
  )
}

function RecordingBlock({ recording }) {
  const [showTranscription, setShowTranscription] = useState(false)

  const dirs = recording.directions
    ?.map(d => DIR_LABELS[d] || d)
    .join(', ')

  return (
    <div className="recording-block">
      <div className="recording-header">
        <span className="recording-role">{ROLE_LABELS[recording.employee_role]}</span>
        <span className="recording-name">{recording.employee_name}</span>
        {dirs && <span className="recording-dirs">({dirs})</span>}
      </div>

      {recording.status === 'done' ? (
        <>
          {recording.score && <ScoreBar score={recording.score} />}

          {recording.analysis && (
            <div className="recording-analysis">
              {recording.analysis.split('\n').map((line, i) => (
                <p key={i}>{line}</p>
              ))}
            </div>
          )}

          {recording.transcription && (
            <div className="transcription-section">
              <button
                className="transcription-toggle"
                onClick={() => setShowTranscription(!showTranscription)}
              >
                {showTranscription ? '▾ Скрыть транскрипцию' : '▸ Показать транскрипцию'}
              </button>
              {showTranscription && (
                <div className="transcription-text">
                  {recording.transcription.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <p className="recording-status">
          {recording.status === 'pending' && 'Ожидает обработки...'}
          {recording.status === 'transcribing' && 'Транскрибация...'}
          {recording.status === 'analyzing' && 'Анализ...'}
          {recording.status === 'error' && 'Ошибка обработки'}
        </p>
      )}
    </div>
  )
}
