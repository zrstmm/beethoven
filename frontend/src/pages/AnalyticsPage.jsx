import { useState, useEffect, useCallback } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { getAnalytics } from '../api/client'
import './AnalyticsPage.css'

const COLORS = {
  bought: '#4caf50',
  not_bought: '#e53935',
  prepayment: '#ffc107',
}

const LABELS = {
  bought: 'Купил',
  not_bought: 'Не купил',
  prepayment: 'Предоплата',
}

function formatDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function getDefaultRange() {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth(), 1)
  return { from: formatDate(from), to: formatDate(now) }
}

export default function AnalyticsPage({ city }) {
  const [range, setRange] = useState(getDefaultRange)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const result = await getAnalytics(city, range.from, range.to)
      setData(result)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [city, range])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const pieData = data ? [
    { name: LABELS.bought, value: data.conversion.bought, key: 'bought' },
    { name: LABELS.not_bought, value: data.conversion.not_bought, key: 'not_bought' },
    { name: LABELS.prepayment, value: data.conversion.prepayment, key: 'prepayment' },
  ].filter(d => d.value > 0) : []

  return (
    <div className="analytics-page">
      <div className="analytics-filters">
        <label>
          С:
          <input
            type="date"
            value={range.from}
            onChange={e => setRange(r => ({ ...r, from: e.target.value }))}
          />
        </label>
        <label>
          По:
          <input
            type="date"
            value={range.to}
            onChange={e => setRange(r => ({ ...r, to: e.target.value }))}
          />
        </label>
      </div>

      {loading && <p className="analytics-loading">Загрузка...</p>}

      {data && !loading && (
        <>
          <div className="analytics-grid">
            <div className="analytics-card">
              <h3>Конверсия</h3>
              <p className="analytics-total">Всего клиентов: {data.conversion.total}</p>
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {pieData.map(entry => (
                        <Cell key={entry.key} fill={COLORS[entry.key]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="analytics-empty">Нет данных за период</p>
              )}
            </div>

            <div className="analytics-card">
              <h3>Топ-3 лучших</h3>
              {data.top_best.length > 0 ? (
                <div className="top-list">
                  {data.top_best.map((item, i) => (
                    <div key={i} className="top-item top-best">
                      <span className="top-rank">#{i + 1}</span>
                      <div className="top-info">
                        <span className="top-client">{item.client_name}</span>
                        <span className="top-employee">{item.employee_name}</span>
                      </div>
                      <span className="top-score">{item.score}/10</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="analytics-empty">Нет данных</p>
              )}

              <h3 style={{ marginTop: 20 }}>Топ-3 худших</h3>
              {data.top_worst.length > 0 ? (
                <div className="top-list">
                  {data.top_worst.map((item, i) => (
                    <div key={i} className="top-item top-worst">
                      <span className="top-rank">#{i + 1}</span>
                      <div className="top-info">
                        <span className="top-client">{item.client_name}</span>
                        <span className="top-employee">{item.employee_name}</span>
                      </div>
                      <span className="top-score">{item.score}/10</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="analytics-empty">Нет данных</p>
              )}
            </div>
          </div>

          {data.common_mistakes.length > 0 && (
            <div className="analytics-card" style={{ marginTop: 16 }}>
              <h3>Частые ошибки</h3>
              <ul className="mistakes-list">
                {data.common_mistakes.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  )
}
