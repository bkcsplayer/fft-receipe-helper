import React, { useState, useEffect } from 'react'
import { CameraCapture } from '@/components/CameraCapture'
import { ResultDisplay } from '@/components/ResultDisplay'
import { Login } from '@/components/Login'
import { BottomNav } from '@/components/BottomNav'
import { HistoryView } from '@/components/HistoryView'
import { SummaryView } from '@/components/SummaryView'

// In development (npm run dev), use absolute localhost URL.
// In production (Docker Nginx), use relative path to allow Nginx to proxy to backend.
export const API_BASE_URL = import.meta.env.PROD ? '' : 'http://localhost:8080'
import { Receipt, Loader2, LogOut, Beaker, Construction } from 'lucide-react'
import { Button } from '@/components/ui/button'
import './custom.css'

function App() {
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [errorStatus, setErrorStatus] = useState(null)
  const [mockMode, setMockMode] = useState(false)
  const [activeTab, setActiveTab] = useState('home') // 'home', 'history', 'settings'

  useEffect(() => {
    // Check local storage for existing session
    const saved = localStorage.getItem('receipt_auth_token')
    const expiresAt = localStorage.getItem('receipt_auth_expires_at')

    if (saved && expiresAt) {
      if (new Date().getTime() < parseInt(expiresAt, 10)) {
        setToken(saved)
      } else {
        // Token expired
        handleLogout()
      }
    } else {
      handleLogout()
    }
  }, [])

  const handleLogin = (newToken) => {
    // Set expiration to 24 hours from now
    const expiresAt = new Date().getTime() + 24 * 60 * 60 * 1000;
    localStorage.setItem('receipt_auth_token', newToken)
    localStorage.setItem('receipt_auth_expires_at', expiresAt.toString())
    setToken(newToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('receipt_auth_token')
    localStorage.removeItem('receipt_auth_expires_at')
    setToken(null)
    setResult(null)
  }

  const handleCapture = async (file) => {
    setLoading(true)
    setErrorStatus(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    if (mockMode) {
      // Simulate backend behavior for UI testing
      setTimeout(() => {
        setResult({
          success: true,
          isPending: true,
          message: "⚠️ 模拟模式：解析成功（未真实调用 API）",
          drive_link: "https://drive.google.com/",
          receipt_data: {
            date: "2026-03-01",
            store_name: "大统华 T&T Supermarket",
            total_price: 36.50,
            tax: 1.50,
            items: [
              { product_name: "散装苹果", price: 5.99 },
              { product_name: "顶级牛排", price: 18.52 },
              { product_name: "新鲜牛奶 2L", price: 4.50 },
              { product_name: "大号生活垃圾袋", price: 5.99 }
            ]
          }
        })
        setLoading(false)
      }, 2000)
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/parse-receipt`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${token}`
        },
        body: formData,
      })

      if (response.status === 401) {
        handleLogout()
        throw new Error('认证过期或失效，请重新登录。')
      }

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const data = await response.json()
      setResult({ ...data, isPending: true })
    } catch (err) {
      console.error(err)
      setErrorStatus(err.message || '网络连接失败，请检查后端运行状态。')
      setResult({
        success: false,
        message: err.message || '网络连接失败，请检查后端运行状态。',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!result || !result.receipt_data) return;
    setLoading(true);
    setErrorStatus(null);

    if (mockMode) {
      setTimeout(() => {
        setResult({
          ...result,
          isPending: false,
          message: "⚠️ 模拟模式：确认保存成功（未真实调用 API）"
        })
        setLoading(false)
      }, 1000)
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/save-receipt`, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          receipt_data: result.receipt_data,
          drive_link: result.drive_link
        }),
      })

      if (response.status === 401) {
        handleLogout()
        throw new Error('认证过期或失效，请重新登录。')
      }

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`)
      }

      const data = await response.json()
      setResult({ ...data, isPending: false })
    } catch (err) {
      console.error(err)
      setErrorStatus(err.message || '保存失败。')
      setResult({
        ...result,
        success: false,
        message: err.message || '保存失败。',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    setResult(null);
    setErrorStatus(null);
  }

  const handleReset = () => {
    setResult(null)
    setErrorStatus(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center">
      {/* Header */}
      <header className="w-full bg-card/60 backdrop-blur-md border-b sticky top-0 z-50">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-primary/10 p-2 rounded-xl text-primary relative">
              <Receipt className="h-6 w-6" />
              {mockMode && <div className="absolute -top-1 -right-1 h-3 w-3 bg-destructive rounded-full" title="模拟模式开启" />}
            </div>
            <h1
              className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-indigo-500 cursor-pointer select-none"
              onDoubleClick={() => setMockMode(!mockMode)}
              title="双击进入/退出无需后端的 UI 模拟模式"
            >
              智能小票管家
            </h1>
          </div>
          <Button variant="ghost" size="sm" onClick={handleLogout} className="text-muted-foreground gap-1 hidden sm:flex">
            <LogOut className="h-4 w-4" /> 退出
          </Button>
          <Button variant="ghost" size="icon" onClick={handleLogout} className="text-muted-foreground sm:hidden">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Main Content Areas based on Tab */}
      <main className="w-full max-w-2xl mx-auto px-4 py-8 flex-1 flex flex-col gap-8 pb-24">
        {mockMode && activeTab === 'home' && !loading && !result && (
          <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm p-3 rounded-lg flex items-center gap-2">
            <Beaker className="h-4 w-4 shrink-0" />
            开发模拟模式已开启（双击左上角文字可关闭）。拍照或选图将直接生成模拟数据，不需要后端 API 支持，方便立即体验 UI。
          </div>
        )}

        {/* --- HOME TAB --- */}
        {activeTab === 'home' && (
          <>
            {!loading && !result && (
              <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-4">
                <div className="text-center space-y-2">
                  <h2 className="text-2xl font-semibold tracking-tight">上传小票</h2>
                  <p className="text-muted-foreground">拍摄或上传购物小票，AI 自动解析并存储至 Google Drive 与 Sheets。</p>
                </div>
                <CameraCapture onCapture={handleCapture} disabled={loading} />
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center flex-1 py-12 gap-6 animate-in fade-in zoom-in-95">
                <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full animate-pulse" />
                  <div className="bg-card border p-4 rounded-2xl shadow-xl relative z-10">
                    <Loader2 className="h-10 w-10 text-primary animate-spin" />
                  </div>
                </div>
                <div className="text-center space-y-2">
                  <h3 className="text-lg font-medium text-transparent bg-clip-text bg-gradient-to-r from-primary to-indigo-500 animate-pulse">
                    🤖 AI 正在进行结构化分析与深度推理中...
                  </h3>
                  <p className="text-sm text-muted-foreground w-64 mx-auto">
                    {result?.isPending ? "正在保存到 Google Sheets..." : "大模型正在运用思维链(CoT)层层解析票据细节，请稍候。"}
                  </p>
                </div>
              </div>
            )}

            {result && !loading && (
              <ResultDisplay
                response={result}
                onReset={handleReset}
                onConfirm={handleSave}
                onCancel={handleCancel}
                isPending={result?.isPending}
              />
            )}
          </>
        )}

        {/* --- MINE TAB --- */}
        {activeTab === 'mine' && (
          <HistoryView token={token} />
        )}

        {/* --- SUMMARY TAB --- */}
        {activeTab === 'summary' && (
          <div className="flex flex-col gap-6 w-full">
            <SummaryView token={token} />

            <div className="mt-8 pt-8 border-t w-full flex flex-col items-center">
              <div className="w-full max-w-xs space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-center">系统账号信息</h3>
                  <p className="text-sm text-muted-foreground mt-1 text-center">
                    目前已登录: <span className="font-mono text-primary bg-primary/10 px-1 py-0.5 rounded">{token ? atob(token).split(':')[0] : ''}</span>
                  </p>
                </div>
                <Button variant="outline" onClick={handleLogout} className="w-full border-destructive/50 text-destructive hover:bg-destructive/10">
                  <LogOut className="h-4 w-4 mr-2" /> 退出登录
                </Button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Bottom Navigation Tab Bar */}
      <BottomNav currentTab={activeTab} onChangeTab={setActiveTab} />
    </div>
  )
}

export default App
