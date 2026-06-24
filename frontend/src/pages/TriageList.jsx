import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listJobs } from '../api/triage'
import { ChevronRight, Plus, ScanLine } from 'lucide-react'
import clsx from 'clsx'

const statusBadge = {
  pending:   'bg-slate-100 text-slate-600 ring-slate-200',
  running:   'bg-blue-50 text-blue-700 ring-blue-200',
  completed: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  failed:    'bg-rose-50 text-rose-700 ring-rose-200',
  partial:   'bg-amber-50 text-amber-700 ring-amber-200',
}

export default function TriageList() {
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['triage-jobs'],
    queryFn: listJobs,
    refetchInterval: 10_000,
  })

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Collections</p>
          <h1 className="page-title">Triage Jobs</h1>
          <p className="page-subtitle">Review recent collection jobs, live progress, logs, and downloadable artifacts.</p>
        </div>
        <Link to="/triage/new" className="btn-primary">
          <Plus size={16} />
          New Job
        </Link>
      </div>

      {isLoading ? (
        <div className="surface p-6 text-sm text-slate-500">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="empty-state">No triage jobs yet.</div>
      ) : (
        <section className="surface overflow-hidden">
          <div className="divide-y divide-slate-100">
            {jobs.map((job) => (
              <Link
                key={job.id}
                to={`/triage/${job.id}`}
                className="group flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-slate-50/80"
              >
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 group-hover:bg-teal-50 group-hover:text-teal-700">
                    <ScanLine size={18} />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">{job.name}</p>
                    <p className="mt-0.5 text-xs text-slate-400">
                      {new Date(job.created_at).toLocaleString()} / {job.selected_nodes?.length ?? 0} nodes
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span className={clsx('status-pill ring-1', statusBadge[job.status] ?? statusBadge.pending)}>
                    {job.status}
                  </span>
                  <ChevronRight size={16} className="text-slate-400 transition-transform group-hover:translate-x-0.5" />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
