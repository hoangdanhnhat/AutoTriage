import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getJob, listArtifacts, downloadArtifact } from '../api/triage'
import { useTriageWebSocket } from '../hooks/useTriageWebSocket'
import TriageProgressTable from '../components/TriageProgressTable'
import { ArrowLeft, CalendarClock, Download, Package, Terminal } from 'lucide-react'
import clsx from 'clsx'

const statusBadge = {
  pending:   'bg-slate-100 text-slate-600 ring-slate-200',
  running:   'bg-blue-50 text-blue-700 ring-blue-200',
  completed: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  failed:    'bg-rose-50 text-rose-700 ring-rose-200',
  partial:   'bg-amber-50 text-amber-700 ring-amber-200',
}

export default function TriageDetail() {
  const { id } = useParams()
  const jobId = Number(id)
  const qc = useQueryClient()

  const [liveData, setLiveData] = useState({})
  const [jobStatus, setJobStatus] = useState(null)
  const [liveLogs, setLiveLogs] = useState({})

  const { data: job, isLoading } = useQuery({
    queryKey: ['triage-job', jobId],
    queryFn: () => getJob(jobId),
    refetchInterval: jobStatus && ['completed', 'failed', 'partial'].includes(jobStatus) ? false : 5000,
  })

  const { data: artifacts } = useQuery({
    queryKey: ['triage-artifacts', jobId],
    queryFn: () => listArtifacts(jobId),
    enabled: ['completed', 'partial', 'failed'].includes(job?.status),
  })

  const onMessage = useCallback((msg) => {
    if (msg.type === 'job_status') {
      setJobStatus(msg.status)
      qc.invalidateQueries({ queryKey: ['triage-job', jobId] })
    } else if (msg.type === 'node_status') {
      setLiveData((prev) => ({
        ...prev,
        [msg.node_ip]: { ...prev[msg.node_ip], status: msg.status, task: msg.task },
      }))
    } else if (msg.type === 'log') {
      setLiveLogs((prev) => ({
        ...prev,
        [msg.node_ip]: [...(prev[msg.node_ip] ?? []), msg.line],
      }))
    }
  }, [jobId, qc])

  useTriageWebSocket(jobId, onMessage)

  const currentStatus = jobStatus ?? job?.status ?? 'pending'

  const handleDownload = async (artifactPath) => {
    const response = await downloadArtifact(jobId, artifactPath)
    const blobUrl = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = artifactPath.split('/').pop() || 'artifact'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(blobUrl)
  }

  if (isLoading) return <div className="page-stack"><div className="surface p-6 text-sm text-slate-500">Loading...</div></div>
  if (!job) return <div className="page-stack"><div className="surface p-6 text-sm text-rose-600">Job not found.</div></div>

  const modules = Object.entries(job.selected_modules ?? {})
    .filter(([, v]) => v)
    .map(([k]) => k.replace('collect_', ''))
    .join(', ')

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <Link to="/triage" className="muted-link mb-3 text-slate-500">
            <ArrowLeft size={16} />
            Triage Jobs
          </Link>
          <p className="page-kicker">Job detail</p>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="page-title">{job.name}</h1>
            <span className={clsx('status-pill ring-1', statusBadge[currentStatus] ?? statusBadge.pending)}>
              {currentStatus === 'running' && <span className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-soft-pulse" />}
              {currentStatus}
            </span>
          </div>
          <p className="page-subtitle">{modules || 'No modules selected'}</p>
        </div>
      </div>

      <section className="grid gap-3 lg:grid-cols-3">
        <MetaItem icon={CalendarClock} label="Created" value={new Date(job.created_at).toLocaleString()} />
        <MetaItem icon={CalendarClock} label="Started" value={job.started_at ? new Date(job.started_at).toLocaleString() : '-'} />
        <MetaItem icon={CalendarClock} label="Completed" value={job.completed_at ? new Date(job.completed_at).toLocaleString() : '-'} />
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="section-title">Node Progress</h2>
        </div>
        <TriageProgressTable
          nodeStatuses={job.node_statuses ?? []}
          liveData={liveData}
        />
      </section>

      {Object.keys(liveLogs).length > 0 && (
        <section className="space-y-3">
          <h2 className="flex items-center gap-2 section-title">
            <Terminal size={16} className="text-teal-700" />
            Live Logs
          </h2>
          <div className="grid gap-3 xl:grid-cols-2">
            {Object.entries(liveLogs).map(([ip, lines]) => (
              <div key={ip} className="overflow-hidden rounded-lg border border-slate-800 bg-slate-950 shadow-sm shadow-slate-300/40">
                <div className="border-b border-white/10 px-4 py-2 font-mono text-xs text-slate-400">{ip}</div>
                <pre className="max-h-60 overflow-auto p-4 text-xs leading-5 text-emerald-300 whitespace-pre-wrap">
                  {lines.join('\n')}
                </pre>
              </div>
            ))}
          </div>
        </section>
      )}

      {artifacts?.files?.length > 0 && (
        <section className="space-y-3">
          <h2 className="flex items-center gap-2 section-title">
            <Package size={16} className="text-teal-700" />
            Artifacts
          </h2>
          <div className="surface overflow-hidden">
            <div className="divide-y divide-slate-100">
              {artifacts.files.map((f) => (
                <div key={f.path} className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm text-slate-800">{f.path}</p>
                    <p className="mt-0.5 text-xs text-slate-400">{(f.size / 1024).toFixed(1)} KB</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDownload(f.path)}
                    className="btn-secondary h-9 self-start sm:self-center"
                  >
                    <Download size={15} />
                    Download
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

function MetaItem({ icon: Icon, label, value }) {
  return (
    <div className="surface flex items-center gap-3 p-4">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase text-slate-400">{label}</p>
        <p className="mt-1 truncate text-sm font-semibold text-slate-900">{value}</p>
      </div>
    </div>
  )
}
