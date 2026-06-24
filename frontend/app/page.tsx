"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken, logout, me } from "@/lib/auth";
import { useLanguage } from "@/lib/i18n";

// Root is a pure router: it never renders a landing page. Staff are sent to the
// dashboard for their role; unauthenticated visitors go to the login screen.
//   manager (clinic director) -> /rahbar
//   operator / admin / super_admin -> /admin
// Customers use the public /yozilish link directly (no login required).
export default function RootRedirect() {
  const router = useRouter();
  const { t } = useLanguage();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    me()
      .then((u) => {
        if (u.force_password_change) {
          router.replace("/change-password");
          return;
        }
        router.replace(u.role === "manager" ? "/rahbar" : "/admin");
      })
      .catch(() => {
        logout();
        router.replace("/login");
      });
  }, [router]);

  return <p className="text-sm text-slate-500">{t("checking_session")}</p>;
}
