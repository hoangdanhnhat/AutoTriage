import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { login } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { Eye, EyeOff, LockKeyhole, ShieldCheck } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const loginStore = useAuthStore((s) => s.login)
  const navigate = useNavigate()

  const { mutate, isPending, isError, error } = useMutation({
    mutationFn: () => login(username, password),
    onSuccess: (data) => {
      loginStore(data.access_token, data.user)
      navigate('/dashboard')
    },
  })

  function handleSubmit(e) {
    e.preventDefault()
    if (username && password) mutate()
  }

  return (
    <div className="grid min-h-screen bg-slate-950 lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden overflow-hidden bg-slate-950 p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(20,184,166,0.22),transparent_42%),radial-gradient(circle_at_70%_30%,rgba(245,158,11,0.16),transparent_30%),linear-gradient(180deg,rgba(15,23,42,0)_0%,rgba(15,23,42,0.9)_100%)]" />
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-teal-400/15 text-teal-200 ring-1 ring-teal-300/25">
            <ShieldCheck size={22} />
          </div>
          <div>
            <p className="text-sm font-semibold">Forensics IR</p>
            <p className="text-xs text-slate-400">Digital triage platform</p>
          </div>
        </div>
        <div className="relative max-w-lg">
          <p className="text-xs font-semibold uppercase text-teal-200">Secure collection</p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight">Coordinate incident triage from one calm workspace.</h1>
          <p className="mt-4 text-sm leading-6 text-slate-300">Inventory status, node selection, collection modules, live logs, and artifacts stay in one operator-focused flow.</p>
        </div>
      </section>

      <main className="flex min-h-screen items-center justify-center px-6 py-10">
        <div className="w-full max-w-md animate-enter">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-teal-700 ring-1 ring-teal-100">
              <ShieldCheck size={21} />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Forensics IR</p>
              <p className="text-xs text-slate-400">Digital triage platform</p>
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-white p-7 shadow-2xl shadow-black/20">
            <div className="mb-7">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                <LockKeyhole size={21} />
              </div>
              <h1 className="text-2xl font-semibold text-slate-950">Sign in</h1>
              <p className="mt-1 text-sm text-slate-500">Access the triage console.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-700">Username</label>
                <input
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-semibold text-slate-700">Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field pr-11"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-1 top-1 inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {isError && (
                <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
                  {error?.response?.data?.detail ?? 'Login failed'}
                </p>
              )}

              <button
                type="submit"
                disabled={isPending}
                className="btn-primary w-full"
              >
                {isPending ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  )
}
