import { getAccessToken } from "./supabase";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

class ApiClient {
  private get baseUrl() {
    const url = process.env.NEXT_PUBLIC_API_URL;
    if (!url) {
      throw new Error("NEXT_PUBLIC_API_URL environment variable is required");
    }
    return url.replace(/\/$/, "") + "/v1";
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = await getAccessToken();
    const headers = new Headers(options.headers);

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errData;
      try {
        errData = await response.json();
      } catch {
        errData = { error: { code: "UNKNOWN_ERROR", message: "An unexpected error occurred." } };
      }
      throw new ApiError(
        errData.error?.code || "HTTP_ERROR",
        errData.error?.message || response.statusText,
        response.status
      );
    }

    return response.json();
  }

  // Upload actions
  uploads = {
    create: async (file: File): Promise<{ upload_id: string; status: string; estimated_seconds: number }> => {
      const formData = new FormData();
      formData.append("file", file);
      return this.request("/uploads", {
        method: "POST",
        body: formData,
      });
    },

    getStatus: async (id: string): Promise<{
      upload_id: string;
      status: "pending" | "processing" | "completed" | "failed";
      step: "ocr" | "classification" | "analysis" | "done" | "failed";
      progress_percent: number;
      error: string | null;
    }> => {
      return this.request(`/uploads/${id}/status`);
    },

    list: async (params: { page: number; per_page: number; q?: string; doc_type?: string; risk_level?: string }): Promise<{
      items: any[];
      total: number;
      page: number;
      per_page: number;
    }> => {
      const query = new URLSearchParams();
      query.set("page", params.page.toString());
      query.set("per_page", params.per_page.toString());
      if (params.q) query.set("q", params.q);
      if (params.doc_type && params.doc_type !== "all") query.set("doc_type", params.doc_type);
      if (params.risk_level && params.risk_level !== "all") query.set("risk_level", params.risk_level);

      return this.request(`/uploads?${query.toString()}`);
    },

    delete: async (id: string): Promise<{ status: string; message: string }> => {
      return this.request(`/uploads/${id}`, {
        method: "DELETE",
      });
    },
  };

  // Analysis actions
  analysis = {
    get: async (id: string): Promise<any> => {
      return this.request(`/analysis/${id}`);
    },

    getDetections: async (id: string): Promise<any> => {
      return this.request(`/uploads/${id}/detections`);
    },

    share: async (id: string, days: number = 7): Promise<{ share_token: string; expires_at: string; share_url: string }> => {
      return this.request(`/analysis/${id}/share?days_to_expire=${days}`, {
        method: "POST",
      });
    },

    getShared: async (token: string): Promise<any> => {
      return this.request(`/analysis/shared/${token}`);
    },

    getExportUrl: (id: string, token: string | null): string => {
      return `${this.baseUrl}/analysis/${id}/export${token ? `?token=${token}` : ""}`;
    },
  };

  // Chat Q&A actions
  chat = {
    getHistory: async (id: string): Promise<{ messages: any[] }> => {
      return this.request(`/chat/${id}`);
    },

    getSuggestions: async (id: string): Promise<{ suggestions: string[] }> => {
      return this.request(`/chat/${id}/suggestions`);
    },

    // Stream chat via POST with Authorization header (no token in URL)
    streamChat: async (id: string, message: string, token: string): Promise<Response> => {
      return fetch(`${this.baseUrl}/chat/${id}/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
      });
    },
  };

  // User preferences & metrics
  users = {
    me: async (): Promise<any> => {
      return this.request("/users/me");
    },

    update: async (data: {
      full_name?: string;
      avatar_url?: string;
      preferred_language?: string;
      ui_language?: string;
      theme?: string;
    }): Promise<any> => {
      return this.request("/users/me", {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },

    getStats: async (): Promise<any> => {
      return this.request("/users/me/stats");
    },

    upgradePlan: async (): Promise<any> => {
      return this.request("/users/me/upgrade", {
        method: "POST",
      });
    },

    deleteAccount: async (): Promise<{ status: string; message: string }> => {
      return this.request("/users/me", {
        method: "DELETE",
      });
    },
  };
}

export const api = new ApiClient();
