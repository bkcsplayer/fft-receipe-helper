import React from 'react';
import { Home, User, PieChart } from 'lucide-react';

export function BottomNav({ currentTab, onChangeTab }) {
    const tabs = [
        { id: 'home', label: 'Home', icon: Home },
        { id: 'mine', label: '我的', icon: User },
        { id: 'summary', label: '汇总情况', icon: PieChart },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-t border-border/50 px-6 pb-safe pt-2">
            <div className="flex justify-around items-center max-w-md mx-auto h-14">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = currentTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => onChangeTab(tab.id)}
                            className={`flex flex-col items-center justify-center w-16 gap-1 transition-all duration-200 ${isActive ? 'text-primary scale-110' : 'text-muted-foreground hover:text-foreground'
                                }`}
                        >
                            <div className={`relative ${isActive ? 'bg-primary/10 p-1.5 rounded-full' : 'p-1.5'}`}>
                                <Icon className={`h-5 w-5 ${isActive ? 'stroke-[2.5px]' : 'stroke-2'}`} />
                            </div>
                            <span className={`text-[10px] font-medium ${isActive ? 'font-bold' : ''}`}>
                                {tab.label}
                            </span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
