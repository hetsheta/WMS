import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

export const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <QueryClientProvider client={queryClient}>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        style: { background: '#1c2030', color: '#e2e8f0', border: '1px solid #2a3050', fontSize: '13px' },
        success: { iconTheme: { primary: '#22c55e', secondary: '#0f1117' } },
        error: { iconTheme: { primary: '#ef4444', secondary: '#0f1117' } },
      }}
    />
  </QueryClientProvider>
)
