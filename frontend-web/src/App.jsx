import { useState, useCallback, useEffect } from 'react'
import { uploadFile, getSummary, getData, getHistory, downloadReport } from './api'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { Bar } from 'react-chartjs-2'
import styles from './App.module.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const DEMO_USER = { username: 'admin', password: 'admin' }

function LoginForm({ onLogin, error }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    onLogin({ username, password })
  }

  return (
    <div className={styles.loginCard}>
      <h1 className={styles.title}>Chemical Equipment Visualizer</h1>
      <p className={styles.subtitle}>Sign in to continue</p>
      <form onSubmit={handleSubmit} className={styles.loginForm}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          className={styles.input}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          className={styles.input}
        />
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" className={styles.btnPrimary}>Sign in</button>
        <button
          type="button"
          className={styles.btnSecondary}
          onClick={() => onLogin(DEMO_USER)}
        >
          Use demo (admin / admin)
        </button>
      </form>
    </div>
  )
}

function DataTable({ data, columns }) {
  if (!data?.length) return <p className={styles.muted}>No data.</p>
  const cols = columns || (data[0] && Object.keys(data[0]))

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{String(c).replace(/_/g, ' ')}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i}>
              {cols.map((col) => (
                <td key={col}>{row[col] ?? '—'}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SummaryCharts({ summary }) {
  if (!summary) return null
  const dist = summary.type_distribution || {}
  const types = Object.keys(dist)
  const values = types.map((t) => dist[t])

  const barData = {
    labels: types,
    datasets: [
      {
        label: 'Count',
        data: values,
        backgroundColor: 'rgba(88, 166, 255, 0.6)',
        borderColor: 'rgb(88, 166, 255)',
        borderWidth: 1,
      },
    ],
  }

  const avg = summary.averages || {}
  const avgData = {
    labels: ['Flowrate', 'Pressure', 'Temperature'],
    datasets: [
      {
        label: 'Average',
        data: [avg.flowrate, avg.pressure, avg.temperature],
        backgroundColor: ['rgba(63, 185, 80, 0.6)', 'rgba(210, 153, 34, 0.6)', 'rgba(248, 81, 73, 0.6)'],
        borderColor: ['rgb(63, 185, 80)', 'rgb(210, 153, 34)', 'rgb(248, 81, 73)'],
        borderWidth: 1,
      },
    ],
  }

  const opts = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
    },
    scales: {
      y: { beginAtZero: true },
    },
  }

  return (
    <div className={styles.charts}>
      <div className={styles.chartBox}>
        <h3>Equipment type distribution</h3>
        <div className={styles.chartInner}>
          <Bar data={barData} options={opts} />
        </div>
      </div>
      <div className={styles.chartBox}>
        <h3>Averages (Flowrate, Pressure, Temperature)</h3>
        <div className={styles.chartInner}>
          <Bar data={avgData} options={opts} />
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [credentials, setCredentials] = useState(null)
  const [authError, setAuthError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [history, setHistory] = useState([])
  const [selected, setSelected] = useState(null)
  const [summary, setSummary] = useState(null)
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [pdfLoading, setPdfLoading] = useState(false)

  const fetchHistory = useCallback(async () => {
    if (!credentials) return
    setLoading(true)
    setError('')
    try {
      const h = await getHistory(credentials)
      setHistory(h)
      if (h.length && !selected) setSelected(h[0])
        else if (selected && !h.find((x) => x.id === selected.id)) setSelected(h[0] || null)
    } catch (e) {
      setError(e.message || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }, [credentials, selected])

  const fetchSummaryAndData = useCallback(async (id) => {
    if (!credentials || !id) return
    setLoading(true)
    setError('')
    try {
      const [s, d] = await Promise.all([
        getSummary(id, credentials),
        getData(id, credentials),
      ])
      setSummary(s)
      setData(d.data || [])
    } catch (e) {
      setError(e.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [credentials])

  const handleLogin = async (creds) => {
    setAuthError('')
    try {
      const h = await getHistory(creds)
      setCredentials(creds)
      setHistory(h)
      if (h.length) setSelected(h[0])
    } catch (e) {
      setAuthError(e.status === 401 ? 'Invalid username or password' : e.message)
    }
  }

  const handleUpload = async (e) => {
    const file = e?.target?.files?.[0]
    if (!file || !credentials) return
    setUploading(true)
    setError('')
    try {
      const res = await uploadFile(file, credentials)
      setHistory((prev) => [res, ...prev.filter((x) => x.id !== res.id)])
      setSelected(res)
      setSummary({ summary: res.summary, filename: res.filename })
      const d = await getData(res.id, credentials)
      setData(d.data || [])
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleSelect = (item) => {
    setSelected(item)
    fetchSummaryAndData(item.id)
  }

  const handlePdf = async () => {
    if (!selected || !credentials) return
    setPdfLoading(true)
    try {
      await downloadReport(selected.id, selected.filename, credentials)
    } catch (e) {
      setError(e.message || 'PDF download failed')
    } finally {
      setPdfLoading(false)
    }
  }

  useEffect(() => {
    if (selected?.id && credentials) fetchSummaryAndData(selected.id)
  }, [selected?.id, credentials, fetchSummaryAndData])

  if (!credentials) {
    return (
      <div className={styles.app}>
        <LoginForm onLogin={handleLogin} error={authError} />
      </div>
    )
  }

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1 className={styles.title}>Chemical Equipment Parameter Visualizer</h1>
        <div className={styles.headerRight}>
          <label className={styles.uploadBtn}>
            <input
              type="file"
              accept=".csv"
              onChange={handleUpload}
              disabled={uploading}
              style={{ display: 'none' }}
            />
            {uploading ? 'Uploading…' : 'Upload CSV'}
          </label>
          <button
            type="button"
            className={styles.btnSecondary}
            onClick={fetchHistory}
            disabled={loading}
          >
            Refresh history
          </button>
          <span className={styles.user}>{credentials.username}</span>
          <button
            type="button"
            className={styles.btnSecondary}
            onClick={() => setCredentials(null)}
          >
            Sign out
          </button>
        </div>
      </header>

      <main className={styles.main}>
        {error && <div className={styles.bannerError}>{error}</div>}

        <aside className={styles.sidebar}>
          <h2>History (last 5)</h2>
          {loading && !history.length ? (
            <p className={styles.muted}>Loading…</p>
          ) : (
            <ul className={styles.historyList}>
              {history.map((item) => (
                <li
                  key={item.id}
                  className={selected?.id === item.id ? styles.selected : ''}
                  onClick={() => handleSelect(item)}
                >
                  <span className={styles.histName}>{item.filename}</span>
                  <span className={styles.histMeta}>{item.summary?.total_count ?? 0} rows</span>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div className={styles.content}>
          {selected && (
            <>
              <div className={styles.toolbar}>
                <h2>{selected.filename}</h2>
                <button
                  type="button"
                  className={styles.btnPrimary}
                  onClick={handlePdf}
                  disabled={pdfLoading}
                >
                  {pdfLoading ? 'Generating…' : 'Download PDF report'}
                </button>
              </div>
              {summary && (
                <section className={styles.section}>
                  <h3>Summary</h3>
                  <p>
                    Total: <strong>{summary.summary?.total_count ?? summary.total_count}</strong>
                    {' · '}
                    Averages — Flowrate: <strong>{summary.summary?.averages?.flowrate ?? summary.averages?.flowrate}</strong>
                    , Pressure: <strong>{summary.summary?.averages?.pressure ?? summary.averages?.pressure}</strong>
                    , Temperature: <strong>{summary.summary?.averages?.temperature ?? summary.averages?.temperature}</strong>
                  </p>
                  <SummaryCharts summary={summary.summary || summary} />
                </section>
              )}
              <section className={styles.section}>
                <h3>Data table</h3>
                <DataTable data={data} />
              </section>
            </>
          )}
          {!selected && !loading && (
            <p className={styles.muted}>Upload a CSV or select an item from history.</p>
          )}
        </div>
      </main>
    </div>
  )
}
