import React, { useState, useEffect } from 'react'
import { API_BASE_URL } from '../App' // Refactored API URL exported from App
import { Loader2, AlertCircle, ReceiptText, ExternalLink, Calendar, MapPin, Receipt } from 'lucide-react'

export function HistoryView({ token }) {
    const [data, setData] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // Format current month for default fetching
    const today = new Date()
    const defaultMonthStr = `${today.getFullYear()}/${String(today.getMonth() + 1).padStart(2, '0')}`
    const [currentMonthStr, setCurrentMonthStr] = useState(defaultMonthStr)

    useEffect(() => {
        fetchHistory(currentMonthStr)
    }, [token, currentMonthStr])

    const fetchHistory = async (monthStr) => {
        setLoading(true)
        setError(null)
        try {
            // In development against React fast refresh, fallback to absolute URL if needed
            const response = await fetch(`${API_BASE_URL}/api/history?month=${encodeURIComponent(monthStr)}`, {
                headers: {
                    'Authorization': `Basic ${token}`
                }
            })

            if (!response.ok) {
                throw new Error(`Failed to fetch: ${response.status}`)
            }

            const jsonData = await response.json()
            // Google sheets data might be chronological, we want reverse chronological (newest first)
            if (Array.isArray(jsonData)) {
                setData(jsonData.reverse())
            } else {
                setData([])
            }
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
                <p className="text-muted-foreground text-sm">正在拉取您的消费记录...</p>
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

    // Format the raw sheet data into grouped items by receipt for better display
    const groupedReceipts = {}
    data.forEach((row, index) => {
        // We group by "小票图片链接(Drive)" since that is unique per receipt
        const driveLink = row["小票图片链接(Drive)"] || `receipt-${index}`
        if (!groupedReceipts[driveLink]) {
            groupedReceipts[driveLink] = {
                date: row["日期"] || "未知日期",
                store: row["店名"] || "未知商店",
                uploader: row["上传者"] || "",
                totalPrice: row["总价(小票级)"] || "",
                tax: row["税费(小票级)"] || "",
                driveLink: driveLink,
                items: []
            }
        }

        // Skip empty items that might just be padding rows
        if (row["商品名称"]) {
            groupedReceipts[driveLink].items.push({
                name: row["商品名称"],
                price: row["单价"] || "0.00"
            })
        }
    })

    const receiptList = Object.values(groupedReceipts)

    return (
        <div className="flex flex-col animate-in fade-in slide-in-from-bottom-4 gap-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-semibold tracking-tight">我的流水</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        记录明细
                    </p>
                </div>
                <div className="flex flex-col items-end gap-1">
                    <input
                        type="month"
                        value={currentMonthStr.replace('/', '-')}
                        onChange={(e) => {
                            if (e.target.value) {
                                setCurrentMonthStr(e.target.value.replace('-', '/'))
                            }
                        }}
                        className="bg-card border text-sm rounded-md px-2 py-1 focus:ring-1 focus:ring-primary outline-none text-foreground color-scheme-dark"
                        style={{ colorScheme: 'dark' }}
                    />
                    <div className="bg-primary/10 text-primary px-3 py-0.5 rounded-full text-xs font-medium mt-1">
                        {receiptList.length} 单
                    </div>
                </div>
            </div>

            {receiptList.length === 0 ? (
                <div className="bg-card border rounded-2xl p-10 text-center text-muted-foreground shadow-sm mt-4">
                    <ReceiptText className="h-10 w-10 mx-auto mb-3 opacity-50" />
                    <p>本月还没有录入任何小票</p>
                    <p className="text-sm mt-1">赶快去上传第一张吧！</p>
                </div>
            ) : (
                <div className="grid gap-4">
                    {receiptList.map((receipt, idx) => (
                        <div key={idx} className="bg-card border rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                            {/* Receipt Header */}
                            <div className="p-4 border-b bg-muted/30 flex justify-between items-start">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2 font-medium text-lg">
                                        <MapPin className="h-4 w-4 text-primary" />
                                        {receipt.store}
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                        <Calendar className="h-3.5 w-3.5" />
                                        {receipt.date}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-lg font-bold font-mono text-primary">
                                        ${receipt.totalPrice}
                                    </div>
                                    {receipt.tax && (
                                        <div className="text-xs text-muted-foreground">
                                            包含税費 ${receipt.tax}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Receipt Items */}
                            <div className="p-4 bg-background">
                                <div className="space-y-2.5">
                                    {receipt.items.map((item, itemIdx) => (
                                        <div key={itemIdx} className="flex justify-between items-center text-sm">
                                            <span className="text-foreground/80 line-clamp-1 pr-4">{item.name}</span>
                                            <span className="font-mono tabular-nums">${item.price}</span>
                                        </div>
                                    ))}
                                </div>

                                {receipt.driveLink && receipt.driveLink.startsWith('http') && (
                                    <div className="mt-4 pt-4 border-t w-full flex justify-end">
                                        <a
                                            href={receipt.driveLink}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="text-xs flex items-center gap-1.5 text-primary hover:underline"
                                        >
                                            <Receipt className="h-3 w-3" />
                                            查看原票据
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
