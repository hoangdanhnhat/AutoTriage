import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listInventories, deleteInventory } from '../api/inventories'
import InventoryUploader from '../components/InventoryUploader'
import { ChevronRight, Database, Plus, Trash2 } from 'lucide-react'

export default function Inventories() {
  const [showUpload, setShowUpload] = useState(false)
  const qc = useQueryClient()

  const { data: inventories = [], isLoading } = useQuery({
    queryKey: ['inventories'],
    queryFn: listInventories,
  })

  const { mutate: doDelete } = useMutation({
    mutationFn: deleteInventory,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['inventories'] }),
  })

  function confirmDelete(inv) {
    if (window.confirm(`Delete inventory "${inv.name}"?`)) doDelete(inv.id)
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Assets</p>
          <h1 className="page-title">Inventories</h1>
          <p className="page-subtitle">Upload Ansible inventories and inspect the nodes available for collection.</p>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="btn-primary"
        >
          <Plus size={16} />
          Upload Inventory
        </button>
      </div>

      {showUpload && (
        <section className="surface p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="section-title">Upload Ansible Inventory</h2>
              <p className="mt-1 text-sm text-slate-500">Accepted formats: INI and plain text.</p>
            </div>
          </div>
          <InventoryUploader onUploaded={() => setShowUpload(false)} />
        </section>
      )}

      {isLoading ? (
        <div className="surface p-6 text-sm text-slate-500">Loading...</div>
      ) : inventories.length === 0 ? (
        <div className="empty-state">No inventories yet. Upload one to get started.</div>
      ) : (
        <section className="surface overflow-hidden">
          <div className="divide-y divide-slate-100">
            {inventories.map((inv) => (
              <div key={inv.id} className="group flex items-center justify-between gap-4 px-5 py-4 transition-colors hover:bg-slate-50/80">
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600 group-hover:bg-teal-50 group-hover:text-teal-700">
                    <Database size={18} />
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">{inv.name}</p>
                    <p className="mt-0.5 text-xs text-slate-400">
                      {new Date(inv.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Link
                    to={`/inventories/${inv.id}`}
                    className="muted-link"
                  >
                    View <ChevronRight size={15} />
                  </Link>
                  <button
                    onClick={() => confirmDelete(inv)}
                    className="icon-button hover:bg-rose-50 hover:text-rose-600"
                    aria-label={`Delete ${inv.name}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
