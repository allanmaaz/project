"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserSupabaseClient } from "../../lib/supabase";
import Sidebar from "../../components/layout/Sidebar";
import MobileNav from "../../components/layout/MobileNav";
import { Loader2 } from "lucide-react";
import ErrorBoundary from "../../components/ErrorBoundary";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const supabase = createBrowserSupabaseClient();

  useEffect(() => {
    const checkAuth = async () => {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        router.push("/login");
      } else {
        setIsAuthenticated(true);
      }
      setIsLoading(false);
    };
    checkAuth();
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-base">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base text-foreground" suppressHydrationWarning>
      {/* Desktop Navigation */}
      <Sidebar />

      {/* Main page layout */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto relative pb-16 lg:pb-0">
        <main className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl mx-auto w-full">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>

        {/* Mobile Navigation */}
        <MobileNav />
      </div>
    </div>
  );
}
