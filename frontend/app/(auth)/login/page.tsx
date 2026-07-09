"use client";

import React, { useState } from "react";
import { createBrowserSupabaseClient } from "../../../lib/supabase";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const supabase = createBrowserSupabaseClient();

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) {
        toast.error(error.message);
        setIsLoading(false);
      }
    } catch {
      toast.error("Failed to connect to Google.");
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-50 mb-1">
          Welcome to Clarify AI
        </h1>
        <p className="text-sm text-muted-foreground">
          Sign in or create your account using Google.
        </p>
      </div>

      <button
        onClick={handleGoogleLogin}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2.5 py-3 px-4 border border-border rounded-xl bg-bg-base hover:bg-neutral-100 dark:hover:bg-neutral-900 text-sm font-semibold transition-all active:scale-[0.98] disabled:opacity-50 shadow-xs"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-brand-500" />
        ) : (
          <svg className="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
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
        )}
        Continue with Google
      </button>

      <p className="text-[10px] text-muted-foreground text-center leading-normal">
        By continuing, you agree to Clarify AI&apos;s Terms of Service and Privacy Policy.
      </p>
    </div>
  );
}
