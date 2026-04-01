import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listInventories, deleteInventory } from '../api/inventories'
import InventoryUploader from '../components/InventoryUploader'
import { Trash2, ChevronRight, Plus } from 'lucide-react'

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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Inventories</h1>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-cyan-600 text-white rounded-md hover:bg-cyan-700"
        >
          <Plus size={15} />
          Upload Inventory
        </button>
      </div>

      {showUpload && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Upload Ansible Inventory</h2>
          <InventoryUploader onUploaded={() => setShowUpload(false)} />
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : inventories.length === 0 ? (
        <div className="bg-white rounded-lg border border-dashed border-gray-300 p-10 text-center">
          <p className="text-gray-400 text-sm">No inventories yet. Upload one to get started.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {inventories.map((inv) => (
            <div key={inv.id} className="flex items-center justify-between px-5 py-4 hover:bg-gray-50">
              <div>
                <p className="text-sm font-semibold text-gray-800">{inv.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {new Date(inv.created_at).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  to={`/inventories/${inv.id}`}
                  className="flex items-center gap-1 text-xs text-cyan-600 hover:underline"
                >
                  View <ChevronRight size={13} />
                </Link>
                <button
                  onClick={() => confirmDelete(inv)}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
