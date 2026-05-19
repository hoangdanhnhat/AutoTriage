import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listJobs } from '../api/triage'
import { Plus, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const statusBadge = {
  pending:   'bg-gray-100 text-gray-600',
  running:   'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  failed:    'bg-red-100 text-red-700',
  partial:   'bg-yellow-100 text-yellow-700',
}

export default function TriageList() {
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ['triage-jobs'],
    queryFn: listJobs,
    refetchInterval: 10_000,
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Triage Jobs</h1>
        <Link
          to="/triage/new"
          className="flex items-center gap-2 px-3 py-2 text-sm bg-cyan-600 text-white rounded-md hover:bg-cyan-700"
        >
          <Plus size={15} />
          New Job
        </Link>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : jobs.length === 0 ? (
        <div className="bg-white rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="text-gray-400 text-sm">No triage jobs yet.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {jobs.map((job) => (
            <Link
              key={job.id}
              to={`/triage/${job.id}`}
              className="flex items-center justify-between px-5 py-4 hover:bg-gray-50"
            >
              <div>
                <p className="text-sm font-semibold text-gray-800">{job.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(job.created_at).toLocaleString()} &middot; {job.selected_nodes?.length ?? 0} nodes
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium capitalize', statusBadge[job.status] ?? statusBadge.pending)}>
                  {job.status}
                </span>
                <ChevronRight size={16} className="text-gray-400" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
