"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createBrowserSupabaseClient } from "../../../lib/supabase";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const supabase = createBrowserSupabaseClient();

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please fill in all fields.");
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        toast.error(error.message);
      } else {
        toast.success("Welcome back!");
        router.push("/dashboard");
      }
    } catch (err) {
      toast.error("An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) {
        toast.error(error.message);
      }
    } catch {
      toast.error("Failed to connect to Google.");
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50 mb-1">
          Welcome back
        </h1>
        <p className="text-sm text-muted-foreground">
          Enter your details to access your account.
        </p>
      </div>

      <button
        onClick={handleGoogleLogin}
        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-border rounded-lg bg-bg-base hover:bg-neutral-100 dark:hover:bg-neutral-900 text-sm font-semibold transition-all"
      >
        {/* Google SVG Icon */}
        <svg className="w-4 h-4" viewBox="0 0 24 24">
          <path
            fill="#ea4335"
            d="M5.266 9.765A7.077 7.077 0 0 1 12 4.909c1.69 0 3.218.6 4.418 1.582L19.91 3C17.782 1.145 15.055 0 12 0 7.33 0 3.357 2.72 1.5 6.705l3.766 3.06z"
          />
          <path
            fill="#4285f4"
            d="M23.49 12.275c0-.825-.075-1.62-.215-2.385H12v4.51h6.44a5.51 5.51 0 0 1-2.395 3.615l3.766 2.92c2.2-2.03 3.68-5.015 3.68-8.66z"
          />
          <path
            fill="#fbbc05"
            d="M5.266 14.235A7.077 7.077 0 0 1 4.91 12c0-.795.138-1.56.356-2.235L1.5 6.705A11.94 11.94 0 0 0 0 12c0 1.92.455 3.73 1.258 5.345l4.008-3.11z"
          />
          <path
            fill="#34a853"
            d="M12 24c3.24 0 5.955-1.075 7.94-2.915l-3.766-2.92c-1.045.7-2.38 1.115-4.174 1.115-3.218 0-5.945-2.175-6.918-5.1L1.258 17.345A11.96 11.96 0 0 0 12 24z"
          />
        </svg>
        Continue with Google
      </button>

      <div className="relative my-6 flex items-center justify-center">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <span className="relative bg-bg-elevated px-3 text-xs uppercase tracking-wider font-semibold text-muted-foreground">
          or
        </span>
      </div>

      <form onSubmit={handleEmailLogin} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
            Email address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@company.com"
            disabled={isLoading}
            className="w-full py-2 px-3 border border-border rounded-lg bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all disabled:opacity-50"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-xs text-brand-500 font-semibold hover:underline"
            >
              Forgot?
            </Link>
          </div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            disabled={isLoading}
            className="w-full py-2 px-3 border border-border rounded-lg bg-bg-base text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all disabled:opacity-50"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 bg-black dark:bg-white text-white dark:text-black font-semibold text-sm rounded-lg hover:opacity-90 transition-all active:scale-[0.98] disabled:opacity-50"
        >
          {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
          Sign In
        </button>
      </form>

      <p className="text-center text-xs text-muted-foreground mt-6">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-brand-500 font-semibold hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}
