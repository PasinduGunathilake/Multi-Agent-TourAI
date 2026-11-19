export interface User {
  id: string;
  email: string;
  display_name?: string | null;
  avatar_url?: string | null;
  email_verified: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<{ error: string | null }>;
  register: (email: string, password: string, displayName?: string) => Promise<{ error: string | null }>;
  logout: () => Promise<void>;
  getToken: () => Promise<string | null>;
  initiateGoogleLogin: () => Promise<void>;
  requestPasswordSetup: (email: string) => Promise<{ success: boolean; message: string }>;
  completePasswordSetup: (token: string, newPassword: string) => Promise<{ error: string | null }>;
}

