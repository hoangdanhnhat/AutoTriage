import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadInventory } from '../api/inventories'
import { FileText, Upload } from 'lucide-react'
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
          'group cursor-pointer rounded-lg border border-dashed p-7 text-center transition-all duration-200',
          dragging
            ? 'border-teal-400 bg-teal-50 shadow-sm shadow-teal-900/10'
            : 'border-slate-300 bg-white/70 hover:-translate-y-0.5 hover:border-teal-400 hover:bg-white'
        )}
      >
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-500 transition-colors group-hover:bg-teal-50 group-hover:text-teal-700">
          {file ? <FileText size={24} /> : <Upload size={24} />}
        </div>
        {file ? (
          <p className="text-sm font-semibold text-slate-800">{file.name}</p>
        ) : (
          <p className="text-sm font-medium text-slate-700">Drop inventory file here or click to browse</p>
        )}
        <p className="mt-1 text-xs text-slate-400">Ansible INI format (.ini, .txt)</p>
        <input
          ref={inputRef}
          type="file"
          accept=".ini,.txt,text/plain"
          className="hidden"
          onChange={(e) => setFile(e.target.files[0])}
        />
      </div>

      {file && (
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            type="text"
            placeholder="Inventory name (optional)"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="input-field flex-1"
          />
          <button
            onClick={() => mutate()}
            disabled={isPending}
            className="btn-primary"
          >
            {isPending ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      )}

      {isError && (
        <p className="text-sm font-medium text-rose-600">
          {error?.response?.data?.detail ?? 'Upload failed'}
        </p>
      )}
    </div>
  )
}
