import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getJob, listArtifacts, artifactDownloadUrl } from '../api/triage'
import { useTriageWebSocket } from '../hooks/useTriageWebSocket'
import TriageProgressTable from '../components/TriageProgressTable'
import { ArrowLeft, Download, Terminal } from 'lucide-react'
import clsx from 'clsx'

const statusBadge = {
  pending:   'bg-gray-100 text-gray-600',
  running:   'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  failed:    'bg-red-100 text-red-700',
  partial:   'bg-yellow-100 text-yellow-700',
}

export default function TriageDetail() {
  const { id } = useParams()
  const jobId = Number(id)
  const qc = useQueryClient()

  // Live per-node state: { [ip]: { status, task, logs: string[] } }
  const [liveData, setLiveData] = useState({})
  const [jobStatus, setJobStatus] = useState(null)
  const [liveLogs, setLiveLogs] = useState({})  // ip -> log lines

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

  if (isLoading) return <p className="text-sm text-gray-500">Loading…</p>
  if (!job) return <p className="text-sm text-red-500">Job not found.</p>

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <Link to="/triage" className="text-gray-400 hover:text-gray-600">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-xl font-bold text-gray-900">{job.name}</h1>
        <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium capitalize', statusBadge[currentStatus] ?? statusBadge.pending)}>
          {currentStatus}
        </span>
      </div>

      {/* Meta */}
      <div className="bg-white rounded-lg border border-gray-200 px-5 py-4 text-sm text-gray-600 space-y-1">
        <p><span className="font-medium">Created:</span> {new Date(job.created_at).toLocaleString()}</p>
        {job.started_at && <p><span className="font-medium">Started:</span> {new Date(job.started_at).toLocaleString()}</p>}
        {job.completed_at && <p><span className="font-medium">Completed:</span> {new Date(job.completed_at).toLocaleString()}</p>}
        <p>
          <span className="font-medium">Modules:</span>{' '}
          {Object.entries(job.selected_modules ?? {})
            .filter(([, v]) => v)
            .map(([k]) => k.replace('collect_', ''))
            .join(', ')}
        </p>
      </div>

      {/* Node progress */}
      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-2">Node Progress</h2>
        <TriageProgressTable
          nodeStatuses={job.node_statuses ?? []}
          liveData={liveData}
        />
      </div>

      {/* Live log stream */}
      {Object.keys(liveLogs).length > 0 && (
        <div>
          <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-2">
            <Terminal size={15} />
            Live Logs
          </h2>
          <div className="space-y-3">
            {Object.entries(liveLogs).map(([ip, lines]) => (
              <div key={ip}>
                <p className="text-xs font-mono text-gray-500 mb-1">{ip}</p>
                <pre className="bg-gray-900 text-green-400 text-xs p-3 rounded overflow-auto max-h-48 whitespace-pre-wrap">
                  {lines.join('\n')}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Artifacts */}
      {artifacts?.files?.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Artifacts</h2>
          <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
            {artifacts.files.map((f) => (
              <div key={f.path} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-mono text-gray-700">{f.path}</p>
                  <p className="text-xs text-gray-400">{(f.size / 1024).toFixed(1)} KB</p>
                </div>
                <a
                  href={artifactDownloadUrl(jobId, f.path)}
                  className="flex items-center gap-1 text-xs text-cyan-600 hover:underline"
                  download
                >
                  <Download size={14} />
                  Download
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
