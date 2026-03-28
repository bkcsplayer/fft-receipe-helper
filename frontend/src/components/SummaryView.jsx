import React, { useState, useEffect } from 'react'
import { API_BASE_URL } from '../App'
import { Loader2, AlertCircle, PieChart as PieChartIcon, TrendingUp, DollarSign, Store, RefreshCcw } from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts'

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1'];

export function SummaryView({ token }) {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const [currentMonthStr, setCurrentMonthStr] = useState('all')
    const [dateMode, setDateMode] = useState('all') // 'all' or 'month'

    useEffect(() => {
        fetchHistory(currentMonthStr)
    }, [token, currentMonthStr])

    const fetchHistory = async (monthStr) => {
        setLoading(true)
        setError(null)
        try {
            const response = await fetch(`${API_BASE_URL}/api/history?month=${encodeURIComponent(monthStr)}&all_users=true`, {
                headers: {
                    'Authorization': `Basic ${token}`
                }
            })

            if (!response.ok) {
                throw new Error(`Failed to fetch: ${response.status}`)
            }

            const jsonData = await response.json()
            setData(Array.isArray(jsonData) ? jsonData : [])
        } catch (err) {
            console.error(err)
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center flex-1 py-12 gap-4 animate-in fade-in">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
                <p className="text-muted-foreground text-sm">正在统筹数据报表...</p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center flex-1 py-12 text-center space-y-4">
                <AlertCircle className="h-10 w-10 text-destructive" />
                <p className="text-destructive font-medium">拉取失败</p>
                <p className="text-sm text-muted-foreground">{error}</p>
                <button
                    onClick={() => fetchHistory(currentMonthStr)}
                    className="text-primary text-sm underline mt-2 hover:opacity-80"
                >
                    重试
                </button>
            </div>
        )
    }

    // --- Data Crunching ---

    let totalSpending = 0
    const storeSpending = {}
    const dateSpending = {}

    // Aggregate data by unique receipt (using drive link as ID)
    const processedReceipts = new Set()

    data.forEach((row) => {
        const driveLink = row["小票图片链接(Drive)"]
        // Only process totals once per receipt
        if (driveLink && !processedReceipts.has(driveLink)) {
            processedReceipts.add(driveLink)

            const priceStr = String(row["总价(小票级)"] || "0").replace(/[^0-9.-]+/g, "")
            const price = parseFloat(priceStr) || 0

            totalSpending += price

            // Store aggregation
            const store = row["店名"] || "未知商店"
            storeSpending[store] = (storeSpending[store] || 0) + price

            // Date aggregation
            const date = row["日期"] || "未知日期"
            dateSpending[date] = (dateSpending[date] || 0) + price
        }
    })

    // Format for Recharts
    const pieData = Object.entries(storeSpending)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6) // Top 6 stores + Others

    // If there are more than 6 stores, group the rest into "Others"
    if (Object.keys(storeSpending).length > 6) {
        const othersValue = Object.entries(storeSpending)
            .sort((a, b) => b.value - a.value)
            .slice(6)
            .reduce((sum, [_, val]) => sum + val, 0)
        pieData.push({ name: '其他', value: othersValue })
    }

    // Format date data chronologically
    const barData = Object.entries(dateSpending)
        .map(([date, amount]) => {
            // Shorten date "2026-03-01" -> "03-01"
            const shortDate = date.split('-').slice(1).join('-') || date
            return { date: shortDate, amount }
        })
        .sort((a, b) => a.date.localeCompare(b.date))

    return (
        <div className="flex flex-col animate-in fade-in slide-in-from-bottom-4 gap-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight">数据汇总</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        账单统计 (全部用户合并)
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => fetchHistory(currentMonthStr)}
                        disabled={loading}
                        className="p-1.5 border rounded-md hover:bg-muted text-muted-foreground transition-colors disabled:opacity-50"
                        title="刷新数据"
                    >
                        <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    <div className="flex bg-card border rounded-md overflow-hidden text-sm" style={{ colorScheme: 'dark' }}>
                        <button
                            onClick={() => { setDateMode('all'); setCurrentMonthStr('all'); }}
                        className={`px-3 py-1 text-xs font-medium transition-colors ${dateMode === 'all' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'}`}
                    >
                        全部
                    </button>
                    <button
                        onClick={() => {
                            setDateMode('month');
                            const today = new Date();
                            setCurrentMonthStr(`${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}`);
                        }}
                        className={`px-3 py-1 text-xs font-medium border-l transition-colors ${dateMode === 'month' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'}`}
                    >
                        按月
                    </button>
                    {dateMode === 'month' && (
                        <input
                            type="month"
                            value={currentMonthStr.replace('/', '-')}
                            onChange={(e) => {
                                if (e.target.value) {
                                    setCurrentMonthStr(e.target.value.replace('-', '/'))
                                }
                            }}
                            className="bg-transparent px-2 py-1 outline-none w-[120px] border-l"
                        />
                    )}
                </div>
                </div>
            </div>

            {data.length === 0 ? (
                <div className="bg-card border rounded-2xl p-10 text-center text-muted-foreground shadow-sm mt-4">
                    <PieChartIcon className="h-10 w-10 mx-auto mb-3 opacity-50" />
                    <p>本月没有消费数据可供汇总</p>
                </div>
            ) : (
                <>
                    {/* Top KPIs */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-card border rounded-2xl p-5 shadow-sm">
                            <div className="flex items-center gap-2 text-muted-foreground mb-2">
                                <DollarSign className="h-4 w-4" />
                                <span className="text-sm font-medium">总支出</span>
                            </div>
                            <div className="text-3xl font-bold font-mono text-foreground">
                                ${totalSpending.toFixed(2)}
                            </div>
                        </div>
                        <div className="bg-card border rounded-2xl p-5 shadow-sm">
                            <div className="flex items-center gap-2 text-muted-foreground mb-2">
                                <Store className="h-4 w-4" />
                                <span className="text-sm font-medium">消费笔数</span>
                            </div>
                            <div className="text-3xl font-bold font-mono text-foreground">
                                {processedReceipts.size}
                                <span className="text-sm text-muted-foreground font-sans ml-1">单</span>
                            </div>
                        </div>
                    </div>

                    {/* Charts */}
                    <div className="bg-card border rounded-2xl p-5 shadow-sm space-y-4">
                        <div className="flex items-center gap-2 font-medium">
                            <TrendingUp className="h-4 w-4 text-primary" />
                            每日消费金字塔
                        </div>
                        <div className="h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                                    <XAxis dataKey="date" tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} />
                                    <YAxis tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }} axisLine={false} tickLine={false} tickFormatter={(val) => `$${val}`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px', color: 'hsl(var(--foreground))' }}
                                        itemStyle={{ color: 'hsl(var(--primary))', fontWeight: 'bold' }}
                                        formatter={(value) => [`$${value.toFixed(2)}`, '支出']}
                                        labelStyle={{ color: 'hsl(var(--muted-foreground))', marginBottom: '4px' }}
                                    />
                                    <Bar dataKey="amount" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} barSize={32} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    <div className="bg-card border rounded-2xl p-5 shadow-sm space-y-4">
                        <div className="flex items-center gap-2 font-medium">
                            <PieChartIcon className="h-4 w-4 text-indigo-500" />
                            商铺支出占比
                        </div>
                        <div className="h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="45%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                        itemStyle={{ fontWeight: 'bold' }}
                                        formatter={(value) => [`$${value.toFixed(2)}`, '金额']}
                                    />
                                    <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: '12px', color: 'hsl(var(--foreground))' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}

        </div>
    )
}
