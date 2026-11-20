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

export interface GenericMessageResponse {
  message: string;
}

export interface VerifyOtpResponse {
  message: string;
  reset_token: string;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  oauthError: string | null;
  clearOAuthError: () => void;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<{ error: string | null }>;
  register: (email: string, password: string, displayName?: string) => Promise<{ error: string | null }>;
  logout: () => Promise<void>;
  getToken: () => Promise<string | null>;
  initiateGoogleLogin: () => Promise<{ error: string | null }>;
  requestPasswordSetup: (email: string) => Promise<{ success: boolean; message: string }>;
  completePasswordSetup: (token: string, newPassword: string) => Promise<{ error: string | null }>;
  checkEmail: (email: string) => Promise<{ exists: boolean; hasPassword: boolean; isOAuth: boolean; message: string }>;
  validateResetEmail: (email: string) => Promise<{ success: boolean; message: string; email?: string }>;
  forgotPassword: (email: string) => Promise<{ success: boolean; message: string }>;
  verifyResetOtp: (email: string, otp: string) => Promise<{ success: boolean; resetToken?: string; message: string }>;
  resetPassword: (resetToken: string, newPassword: string, confirmPassword?: string) => Promise<{ success: boolean; message: string }>;
  resendResetOtp: (email: string) => Promise<{ success: boolean; message: string }>;
}

