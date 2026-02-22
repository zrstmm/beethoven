import { useState, useEffect, useCallback } from 'react'
import { getClients } from '../api/client'
import ClientModal from '../components/ClientModal'
import './AnalysesPage.css'

const DAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const MONTH_NAMES = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
]

const RESULT_COLORS = {
  bought: 'var(--green)',
  not_bought: 'var(--red)',
  prepayment: 'var(--yellow)',
}

const RESULT_LABELS = {
  bought: 'Купил',
  not_bought: 'Не купил',
  prepayment: 'Предоплата',
}

function getMonday(date) {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  d.setDate(diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function formatDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getWeekDays(monday) {
  const days = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    days.push(d)
  }
  return days
}

export default function AnalysesPage({ city }) {
  const [monday, setMonday] = useState(() => getMonday(new Date()))
  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedClient, setSelectedClient] = useState(null)
  const [datePickerOpen, setDatePickerOpen] = useState(false)
  const [datePickerValue, setDatePickerValue] = useState('')

  const weekDays = getWeekDays(monday)

  const fetchClients = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getClients(city, formatDate(monday))
      setClients(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [city, monday])

  useEffect(() => {
    fetchClients()
  }, [fetchClients])

  function prevWeek() {
    const d = new Date(monday)
    d.setDate(d.getDate() - 7)
    setMonday(d)
  }

  function nextWeek() {
    const d = new Date(monday)
    d.setDate(d.getDate() + 7)
    setMonday(d)
  }

  function goToDate(dateStr) {
    setMonday(getMonday(new Date(dateStr)))
    setDatePickerOpen(false)
  }

  function getClientsForDay(date) {
    const dayStr = formatDate(date)
    return clients.filter(c => {
      const cDate = new Date(c.lesson_datetime)
      return formatDate(cDate) === dayStr
    })
  }

  const sunday = weekDays[6]
  const weekLabel = `${monday.getDate()} - ${sunday.getDate()} ${MONTH_NAMES[sunday.getMonth()]} ${sunday.getFullYear()}`

  return (
    <div className="analyses-page">
      <div className="week-nav">
        <button className="week-btn" onClick={prevWeek}>◀</button>
        <span className="week-label">{weekLabel}</span>
        <button className="week-btn" onClick={nextWeek}>▶</button>
        <div className="date-picker-wrap">
          <button className="week-btn calendar-btn" onClick={() => setDatePickerOpen(!datePickerOpen)}>
            📅
          </button>
          {datePickerOpen && (
            <div className="date-picker-dropdown">
              <input
                type="date"
                value={datePickerValue}
                onChange={(e) => setDatePickerValue(e.target.value)}
                autoFocus
              />
              <button
                className="date-picker-go"
                onClick={() => datePickerValue && goToDate(datePickerValue)}
              >
                Перейти
              </button>
            </div>
          )}
        </div>
      </div>

      {loading ? (
        <div className="loading">Загрузка...</div>
      ) : (
        <div className="kanban">
          {weekDays.map((day, i) => {
            const dayClients = getClientsForDay(day)
            const isToday = formatDate(day) === formatDate(new Date())
            return (
              <div key={i} className={`kanban-col ${isToday ? 'today' : ''}`}>
                <div className="kanban-header">
                  <span className="day-name">{DAY_NAMES[i]}</span>
                  <span className="day-date">{day.getDate()}</span>
                </div>
                <div className="kanban-cards">
                  {dayClients.map(client => (
                    <div
                      key={client.id}
                      className="client-card"
                      onClick={() => setSelectedClient(client.id)}
                    >
                      <div className="card-time">
                        {new Date(client.lesson_datetime).toLocaleTimeString('ru', {
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </div>
                      <div className="card-client">{client.name}</div>
                      {client.teacher_name && (
                        <div className="card-employee">🎵 {client.teacher_name}</div>
                      )}
                      {client.manager_name && (
                        <div className="card-employee">💼 {client.manager_name}</div>
                      )}
                      <div className="card-footer">
                        {client.result && (
                          <span
                            className="card-result"
                            style={{ color: RESULT_COLORS[client.result] }}
                          >
                            {RESULT_LABELS[client.result]}
                          </span>
                        )}
                        {(client.teacher_score || client.manager_score) && (
                          <span className="card-score">
                            {client.teacher_score || client.manager_score}/10
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {selectedClient && (
        <ClientModal
          clientId={selectedClient}
          onClose={() => setSelectedClient(null)}
        />
      )}
    </div>
  )
}
