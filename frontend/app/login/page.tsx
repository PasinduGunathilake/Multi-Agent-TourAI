"use client";

import React, { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LoginForm } from "@/components/login-form";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleSuccess = () => {
    const rawReturnUrl =
      searchParams.get("returnUrl") || searchParams.get("redirect") || "/";

    // Prevent open redirect vulnerabilities: ensure path starts with a single /
    // and does not contain protocol scheme or protocol-relative slashes
    let safeUrl = "/";
    if (
      rawReturnUrl.startsWith("/") &&
      !rawReturnUrl.startsWith("//") &&
      !rawReturnUrl.includes("://")
    ) {
      safeUrl = rawReturnUrl;
    }
    router.push(safeUrl);
  };

  return <LoginForm onSuccess={handleSuccess} />;
}

export default function LoginPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-black/95 p-6 md:p-10">
      <div className="w-full max-w-sm md:max-w-4xl">
        <Suspense
          fallback={
            <div className="p-8 text-center text-sm text-white/40 font-mono">
              Loading authentication...
            </div>
          }
        >
          <LoginContent />
        </Suspense>
      </div>
    </div>
  );
}
