import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from './ui/card';
import { ExternalLink, CheckCircle2, AlertCircle, ShoppingBag, Receipt, Calendar, Store } from 'lucide-react';
import { Button } from './ui/button';

export function ResultDisplay({ response, onReset }) {
    if (!response) return null;

    const { success, receipt_data, drive_link, message } = response;

    if (!success) {
        return (
            <Card className="border-destructive/50 bg-destructive/5 w-full animate-in fade-in slide-in-from-bottom-4">
                <CardHeader className="text-destructive flex flex-row items-center gap-2">
                    <AlertCircle className="h-5 w-5" />
                    <CardTitle>处理失败</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-destructive/80">{message}</p>
                </CardContent>
                <CardFooter>
                    <Button variant="outline" onClick={onReset} className="w-full">
                        重试
                    </Button>
                </CardFooter>
            </Card>
        );
    }

    return (
        <Card className="w-full border-primary/20 bg-background/60 backdrop-blur-xl animate-in fade-in slide-in-from-bottom-4 shadow-xl">
            <CardHeader className="bg-primary/5 pb-4 border-b">
                <div className="flex items-center gap-2 text-primary">
                    <CheckCircle2 className="h-5 w-5" />
                    <CardTitle>解析成功</CardTitle>
                </div>
                <p className="text-sm text-muted-foreground mt-2">{message}</p>
            </CardHeader>

            <CardContent className="pt-6 space-y-6">
                {/* Meta Info */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-start gap-2">
                        <Store className="h-4 w-4 mt-1 text-muted-foreground" />
                        <div>
                            <p className="text-xs text-muted-foreground uppercase tracking-wider">店名</p>
                            <p className="font-medium">{receipt_data.store_name || '未知'}</p>
                        </div>
                    </div>
                    <div className="flex items-start gap-2">
                        <Calendar className="h-4 w-4 mt-1 text-muted-foreground" />
                        <div>
                            <p className="text-xs text-muted-foreground uppercase tracking-wider">日期</p>
                            <p className="font-medium">{receipt_data.date || '未知'}</p>
                        </div>
                    </div>
                </div>

                {/* Itemized List */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2 border-b pb-2">
                        <ShoppingBag className="h-4 w-4 text-muted-foreground" />
                        <h4 className="text-sm font-semibold tracking-wide flex-1">商品列表</h4>
                        <span className="text-xs bg-muted px-2 py-1 rounded-full">{receipt_data.items.length} 件</span>
                    </div>

                    <div className="max-h-60 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                        {receipt_data.items.map((item, i) => (
                            <div key={i} className="flex justify-between items-center p-3 sm:p-2 sm:px-3 bg-card rounded-lg border border-border/50 text-sm">
                                <span className="font-medium truncate flex-1 pr-4">{item.product_name}</span>
                                <span className="font-mono text-muted-foreground">${item.price.toFixed(2)}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Totals */}
                <div className="bg-muted/50 rounded-xl p-4 space-y-2 border">
                    <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">税费 (Tax)</span>
                        <span className="font-mono">${receipt_data.tax.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between font-bold text-lg pt-2 border-t mt-2">
                        <span>总计 (Total)</span>
                        <span className="font-mono">${receipt_data.total_price.toFixed(2)}</span>
                    </div>
                </div>
            </CardContent>

            <CardFooter className="flex flex-col sm:flex-row gap-3 bg-muted/20 border-t pt-6">
                {drive_link && (
                    <Button variant="outline" className="w-full sm:w-auto flex-1 gap-2" onClick={() => window.open(drive_link, '_blank')}>
                        <Receipt className="h-4 w-4" />
                        查看原图 (Drive)
                        <ExternalLink className="h-3 w-3 ml-1" />
                    </Button>
                )}
                <Button onClick={onReset} className="w-full sm:w-auto flex-1">
                    继续拍摄
                </Button>
            </CardFooter>
        </Card>
    );
}
