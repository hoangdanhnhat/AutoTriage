import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { login } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { ShieldCheck, Eye, EyeOff } from 'lucide-react'

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
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="w-full max-w-sm bg-white rounded-xl shadow-2xl p-8">
        <div className="flex flex-col items-center mb-8">
          <ShieldCheck size={48} className="text-cyan-600 mb-3" />
          <h1 className="text-2xl font-bold text-gray-900">Forensics IR</h1>
          <p className="text-sm text-gray-500 mt-1">Digital Triage Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 pr-9 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-2.5 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {isError && (
            <p className="text-sm text-red-600">
              {error?.response?.data?.detail ?? 'Login failed'}
            </p>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full py-2.5 bg-cyan-600 text-white text-sm font-semibold rounded-md hover:bg-cyan-700 disabled:opacity-50 transition-colors"
          >
            {isPending ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
