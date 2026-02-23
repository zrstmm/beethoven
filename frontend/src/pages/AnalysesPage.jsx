import { useState, useEffect, useCallback } from 'react'
import { getClients, deleteClient } from '../api/client'
import { ChevronLeft, ChevronRight, Calendar, Music, Briefcase, Pencil, Trash2 } from 'lucide-react'
import ClientModal from '../components/ClientModal'
import EditClientModal from '../components/EditClientModal'
import './AnalysesPage.css'

const DAY_NAMES = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const MONTH_NAMES = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
]

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
  const [editingClient, setEditingClient] = useState(null)
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

  async function handleDelete(clientId, e) {
    e.stopPropagation()
    if (!confirm('Удалить клиента и все записи?')) return
    try {
      await deleteClient(clientId)
      fetchClients()
    } catch (err) {
      console.error(err)
    }
  }

  function handleEdit(client, e) {
    e.stopPropagation()
    setEditingClient(client)
  }

  const sunday = weekDays[6]
  const weekLabel = `${monday.getDate()} - ${sunday.getDate()} ${MONTH_NAMES[sunday.getMonth()]} ${sunday.getFullYear()}`

  return (
    <div className="analyses-page">
      <div className="week-nav">
        <button className="week-btn" onClick={prevWeek}><ChevronLeft size={16} /></button>
        <span className="week-label">{weekLabel}</span>
        <button className="week-btn" onClick={nextWeek}><ChevronRight size={16} /></button>
        <div className="date-picker-wrap">
          <button className="week-btn calendar-btn" onClick={() => setDatePickerOpen(!datePickerOpen)}>
            <Calendar size={16} />
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
                      <div className="card-actions">
                        <button className="card-action-btn" onClick={(e) => handleEdit(client, e)} title="Редактировать">
                          <Pencil size={12} />
                        </button>
                        <button className="card-action-btn card-action-delete" onClick={(e) => handleDelete(client.id, e)} title="Удалить">
                          <Trash2 size={12} />
                        </button>
                      </div>
                      <div className="card-time">
                        {new Date(client.lesson_datetime).toLocaleTimeString('ru', {
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </div>
                      <div className="card-client">{client.name}</div>
                      {client.teacher_name && (
                        <div className="card-employee">
                          <Music size={11} />
                          <span>{client.teacher_name}</span>
                        </div>
                      )}
                      {client.manager_name && (
                        <div className="card-employee">
                          <Briefcase size={11} />
                          <span>{client.manager_name}</span>
                        </div>
                      )}
                      <div className="card-footer">
                        {client.result && (
                          <span className={`card-result-pill ${client.result}`}>
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

      {editingClient && (
        <EditClientModal
          client={editingClient}
          onClose={() => setEditingClient(null)}
          onSaved={() => { setEditingClient(null); fetchClients() }}
        />
      )}
    </div>
  )
}
