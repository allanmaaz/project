"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, History, BarChart2, Settings, UploadCloud } from "lucide-react";

export default function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { label: "Home", href: "/dashboard", icon: LayoutDashboard },
    { label: "History", href: "/history", icon: History },
    { label: "Upload", href: "/upload", icon: UploadCloud, isCenter: true },
    { label: "Stats", href: "/stats", icon: BarChart2 },
    { label: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <div className="lg:hidden fixed bottom-0 left-0 right-0 h-16 bg-bg-elevated border-t border-border flex items-center justify-around px-4 z-40 pb-safe shadow-lg">
      {navItems.map((item) => {
        const isActive = pathname === item.href;
        const Icon = item.icon;

        if (item.isCenter) {
          return (
            <Link
              key={item.href}
              href={item.href}
              className="relative -top-4 w-12 h-12 rounded-full bg-black dark:bg-white text-white dark:text-black flex items-center justify-center shadow-lg border-4 border-bg-base hover:scale-105 active:scale-95 transition-all z-50"
            >
              <Icon className="w-5.5 h-5.5" />
            </Link>
          );
        }

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-col items-center justify-center flex-1 h-full gap-1 text-[10px] font-semibold transition-all ${
              isActive ? "text-brand-500" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon className={`w-5 h-5 ${isActive ? "text-brand-500" : ""}`} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </div>
  );
}
