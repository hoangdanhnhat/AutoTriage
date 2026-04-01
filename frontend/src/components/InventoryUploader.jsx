import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadInventory } from '../api/inventories'
import { Upload } from 'lucide-react'
import clsx from 'clsx'

export default function InventoryUploader({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [name, setName] = useState('')
  const [file, setFile] = useState(null)
  const inputRef = useRef(null)
  const qc = useQueryClient()

  const { mutate, isPending, isError, error } = useMutation({
    mutationFn: () => uploadInventory(name || file.name, file),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['inventories'] })
      setFile(null)
      setName('')
      onUploaded?.(data)
    },
  })

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          dragging ? 'border-cyan-500 bg-cyan-50' : 'border-gray-300 hover:border-cyan-400'
        )}
      >
        <Upload size={28} className="mx-auto mb-2 text-gray-400" />
        {file
          ? <p className="text-sm text-gray-700 font-medium">{file.name}</p>
          : <p className="text-sm text-gray-500">Drop inventory file here or click to browse</p>
        }
        <p className="text-xs text-gray-400 mt-1">Ansible INI format (.ini, .txt)</p>
        <input
          ref={inputRef}
          type="file"
          accept=".ini,.txt,text/plain"
          className="hidden"
          onChange={(e) => setFile(e.target.files[0])}
        />
      </div>

      {file && (
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Inventory name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
          />
          <button
            onClick={() => mutate()}
            disabled={isPending}
            className="px-4 py-2 bg-cyan-600 text-white text-sm rounded-md hover:bg-cyan-700 disabled:opacity-50"
          >
            {isPending ? 'Uploading…' : 'Upload'}
          </button>
        </div>
      )}

      {isError && (
        <p className="text-sm text-red-600">{error?.response?.data?.detail ?? 'Upload failed'}</p>
      )}
    </div>
  )
}
