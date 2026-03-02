import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from './ui/card';
import { Button } from './ui/button';
import { Receipt, Lock, User, AlertCircle } from 'lucide-react';

export function Login({ onLogin }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        // Hardcoded logic per user request
        setTimeout(() => {
            if ((username === 'admin' || username === 'admin2') && password === '1q2w3e4R') {
                // Create basic auth token
                const token = btoa(`${username}:${password}`);
                onLogin(token);
            } else {
                setError('账号或密码错误');
            }
            setLoading(false);
        }, 600); // Simulate slight network delay for effect
    };

    return (
        <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-sm">
                <div className="flex flex-col items-center mb-8 animate-in slide-in-from-bottom-6 fade-in duration-500">
                    <div className="bg-primary/10 p-4 rounded-2xl text-primary mb-4 shadow-inner">
                        <Receipt className="h-10 w-10" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-primary to-indigo-400">
                        智能小票管家
                    </h1>
                    <p className="text-muted-foreground mt-2 text-sm font-medium">
                        全栈 OCR 记账系统 (Vibe Version)
                    </p>
                </div>

                <Card className="border-primary/20 bg-background/60 backdrop-blur-xl shadow-2xl animate-in slide-in-from-bottom-8 fade-in duration-700">
                    <form onSubmit={handleSubmit}>
                        <CardHeader className="space-y-1 pb-4">
                            <CardTitle className="text-xl">安全登录</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {error && (
                                <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-lg flex items-center gap-2 animate-in shake">
                                    <AlertCircle className="h-4 w-4" />
                                    {error}
                                </div>
                            )}

                            <div className="space-y-2 relative">
                                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider ml-1">
                                    账号
                                </label>
                                <div className="relative">
                                    <User className="absolute left-3 top-2.5 h-5 w-5 text-muted-foreground/50" />
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="flex h-10 w-full rounded-md border border-input bg-background/50 px-10 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all"
                                        placeholder="输入分配的账号"
                                        autoComplete="username"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2 relative">
                                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider ml-1">
                                    密码
                                </label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-2.5 h-5 w-5 text-muted-foreground/50" />
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="flex h-10 w-full rounded-md border border-input bg-background/50 px-10 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all"
                                        placeholder="••••••••"
                                        autoComplete="current-password"
                                        required
                                    />
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="pt-2">
                            <Button type="submit" className="w-full text-md h-11 transition-all active:scale-[0.98]" disabled={loading}>
                                {loading ? '验证中...' : '进入管家'}
                            </Button>
                        </CardFooter>
                    </form>
                </Card>
            </div>
        </div>
    );
}
