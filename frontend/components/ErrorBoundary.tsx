"use client";

import { Component, ReactNode, ErrorInfo } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ error, errorInfo });
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[300px] p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-danger-50 flex items-center justify-center mb-4">
            <AlertTriangle className="w-8 h-8 text-danger-500" />
          </div>
          <h2 className="text-lg font-semibold text-foreground mb-2">Something went wrong</h2>
          <p className="text-sm text-muted-foreground mb-4 max-w-md">
            We encountered an unexpected error. Please try refreshing the page or contact support if the problem persists.
          </p>
          <details className="text-xs text-muted-foreground mb-4 max-w-md text-left bg-bg-sunken p-3 rounded-lg">
            <summary className="cursor-pointer font-mono mb-1">Error Details</summary>
            <pre className="whitespace-pre-wrap overflow-auto max-h-40">{this.state.error?.message}</pre>
            {this.state.errorInfo?.componentStack && (
              <>
                <hr className="my-2 border-border" />
                <summary className="cursor-pointer font-mono mb-1">Component Stack</summary>
                <pre className="whitespace-pre-wrap overflow-auto max-h-40">{this.state.errorInfo.componentStack}</pre>
              </>
            )}
          </details>
          <button
            onClick={this.handleRetry}
            className="px-4 py-2 bg-brand-500 text-white font-semibold rounded-xl hover:opacity-90 transition-all flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;