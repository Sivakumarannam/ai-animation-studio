import { useAuthStore } from '@/stores/auth'

export function SettingsPage() {
  const user = useAuthStore((s) => s.user)

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      <div className="card p-6 mb-4">
        <h2 className="text-base font-semibold text-gray-100 mb-4">Account</h2>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">Full Name</span>
            <span className="text-gray-200">{user?.full_name}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">Email</span>
            <span className="text-gray-200">{user?.email}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-800">
            <span className="text-gray-400">Plan</span>
            <span className="badge-blue">{user?.plan}</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-400">Default Language</span>
            <span className="text-gray-200">{user?.language}</span>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h2 className="text-base font-semibold text-gray-100 mb-4">Platform</h2>
        <p className="text-sm text-gray-500">
          AI provider configuration, API keys, and infrastructure settings will be available in a future update.
        </p>
      </div>
    </div>
  )
}
