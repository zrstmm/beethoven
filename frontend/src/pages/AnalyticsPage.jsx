import { useState, useEffect, useCallback } from 'react'
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  BarChart, Bar,
} from 'recharts'
import { getAnalytics } from '../api/client'
import './AnalyticsPage.css'

const COLORS = {
  bought: '#30d158',
  not_bought: '#ff453a',
  prepayment: '#ffd60a',
}

const LABELS = {
  bought: 'Купил',
  not_bought: 'Не купил',
  prepayment: 'Предоплата',
}

const ROLE_LABELS = {
  teacher: 'Преподаватель',
  sales_manager: 'МОП',
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

  const conversionRate = data && data.conversion.total > 0
    ? Math.round((data.conversion.bought / data.conversion.total) * 100)
    : 0

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
        <div className="analytics-sections">
          {/* Row 1: Conversion donut + Score distribution */}
          <div className="analytics-grid-2">
            <div className="analytics-card">
              <h3>Конверсия</h3>
              <p className="analytics-total">Всего клиентов: {data.conversion.total}</p>
              {pieData.length > 0 ? (
                <div className="donut-wrap">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={pieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        strokeWidth={0}
                      >
                        {pieData.map(entry => (
                          <Cell key={entry.key} fill={COLORS[entry.key]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#141414', border: '1px solid #1d1d1f', borderRadius: 8, fontSize: 13 }}
                        itemStyle={{ color: '#f5f5f7' }}
                      />
                      <Legend
                        formatter={(value) => <span style={{ color: '#86868b', fontSize: 12 }}>{value}</span>}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="donut-center">
                    <span className="donut-pct">{conversionRate}%</span>
                    <span className="donut-label">конверсия</span>
                  </div>
                </div>
              ) : (
                <p className="analytics-empty">Нет данных за период</p>
              )}
            </div>

            <div className="analytics-card">
              <h3>Распределение оценок</h3>
              {data.score_distribution && data.score_distribution.some(d => d.count > 0) ? (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.score_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1d1d1f" />
                    <XAxis dataKey="score" stroke="#86868b" fontSize={12} />
                    <YAxis stroke="#86868b" fontSize={12} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ background: '#141414', border: '1px solid #1d1d1f', borderRadius: 8, fontSize: 13 }}
                      itemStyle={{ color: '#f5f5f7' }}
                    />
                    <Bar dataKey="count" name="Записей" fill="#fff" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="analytics-empty">Нет данных</p>
              )}
            </div>
          </div>

          {/* Row 2: Weekly trend (full width) */}
          {data.weekly_trends && data.weekly_trends.length > 0 && (
            <div className="analytics-card analytics-full">
              <h3>Тренд конверсии по неделям</h3>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={data.weekly_trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="convGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#fff" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#fff" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1d1d1f" />
                  <XAxis
                    dataKey="week_start"
                    stroke="#86868b"
                    fontSize={11}
                    tickFormatter={(v) => { const d = new Date(v); return `${d.getDate()}.${String(d.getMonth()+1).padStart(2,'0')}` }}
                  />
                  <YAxis stroke="#86868b" fontSize={11} unit="%" />
                  <Tooltip
                    contentStyle={{ background: '#141414', border: '1px solid #1d1d1f', borderRadius: 8, fontSize: 13 }}
                    itemStyle={{ color: '#f5f5f7' }}
                    formatter={(v) => [`${v}%`, 'Конверсия']}
                    labelFormatter={(v) => { const d = new Date(v); return `Неделя с ${d.getDate()}.${String(d.getMonth()+1).padStart(2,'0')}` }}
                  />
                  <Area
                    type="monotone"
                    dataKey="conversion_rate"
                    stroke="#fff"
                    strokeWidth={2}
                    fill="url(#convGrad)"
                    name="Конверсия"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Row 3: Employee performance (full width) */}
          {data.employee_performance && data.employee_performance.length > 0 && (
            <div className="analytics-card analytics-full">
              <h3>Рейтинг сотрудников</h3>
              <table className="perf-table">
                <thead>
                  <tr>
                    <th>Сотрудник</th>
                    <th>Роль</th>
                    <th>Записей</th>
                    <th>Ср. оценка</th>
                    <th style={{ width: '30%' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {data.employee_performance.map((emp, i) => {
                    const pct = (emp.avg_score / 10) * 100
                    const color = emp.avg_score >= 7 ? 'var(--green)' : emp.avg_score >= 4 ? 'var(--yellow)' : 'var(--red)'
                    return (
                      <tr key={i}>
                        <td className="perf-name">{emp.employee_name}</td>
                        <td className="perf-role">{ROLE_LABELS[emp.role] || emp.role}</td>
                        <td className="perf-count">{emp.recording_count}</td>
                        <td className="perf-score" style={{ color }}>{emp.avg_score}</td>
                        <td>
                          <div className="perf-bar">
                            <div className="perf-bar-fill" style={{ width: `${pct}%`, background: color }} />
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Row 4: Direction breakdown + Top best/worst */}
          <div className="analytics-grid-2">
            {data.direction_breakdown && data.direction_breakdown.length > 0 && (
              <div className="analytics-card">
                <h3>По направлениям</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={data.direction_breakdown} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1d1d1f" />
                    <XAxis dataKey="direction" stroke="#86868b" fontSize={11} />
                    <YAxis stroke="#86868b" fontSize={11} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ background: '#141414', border: '1px solid #1d1d1f', borderRadius: 8, fontSize: 13 }}
                      itemStyle={{ color: '#f5f5f7' }}
                    />
                    <Bar dataKey="bought" name="Купил" fill={COLORS.bought} stackId="a" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="not_bought" name="Не купил" fill={COLORS.not_bought} stackId="a" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="prepayment" name="Предоплата" fill={COLORS.prepayment} stackId="a" radius={[4, 4, 0, 0]} />
                    <Legend
                      formatter={(value) => <span style={{ color: '#86868b', fontSize: 11 }}>{value}</span>}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            <div className="analytics-card">
              <h3>Топ-3 лучших</h3>
              {data.top_best.length > 0 ? (
                <div className="top-list">
                  {data.top_best.map((item, i) => (
                    <div key={i} className="top-item">
                      <span className="top-rank">#{i + 1}</span>
                      <div className="top-info">
                        <span className="top-client">{item.client_name}</span>
                        <span className="top-employee">{item.employee_name}</span>
                      </div>
                      <span className="top-score top-score-best">{item.score}/10</span>
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
                    <div key={i} className="top-item">
                      <span className="top-rank">#{i + 1}</span>
                      <div className="top-info">
                        <span className="top-client">{item.client_name}</span>
                        <span className="top-employee">{item.employee_name}</span>
                      </div>
                      <span className="top-score top-score-worst">{item.score}/10</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="analytics-empty">Нет данных</p>
              )}
            </div>
          </div>

          {/* Row 5: Common mistakes */}
          {data.common_mistakes.length > 0 && (
            <div className="analytics-card analytics-full">
              <h3>Частые ошибки</h3>
              <ul className="mistakes-list">
                {data.common_mistakes.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
