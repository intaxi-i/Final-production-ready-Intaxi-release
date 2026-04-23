"use client";

import { useEffect, useState } from "react";
import ActionCard from "@/components/ActionCard";
import BottomNav from "@/components/BottomNav";
import PageHeader from "@/components/PageHeader";
import { useApp } from "@/context/AppContext";
import { APP_ROUTES } from "@/lib/constants";
import { t } from "@/lib/i18n";

export default function IntercityPage() {
  const { lang, user } = useApp();
  const [forcedRole, setForcedRole] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setForcedRole(params.get("role") || "");
  }, []);

  const role = forcedRole || user?.active_role || "passenger";

  return (
    <main className="page">
      <div className="container stack">
        <PageHeader title={t(lang, "intercity")} subtitle={t(lang, "intercityDescription")} />

        {role === "driver" ? (
          <>
            <ActionCard href={APP_ROUTES.intercityRoute} title={t(lang, "createRoute")} text={t(lang, "details")} />
            <ActionCard href={APP_ROUTES.intercityOffers} title={t(lang, "availableOffers")} text={t(lang, "tabsRequests")} />
            <ActionCard href={APP_ROUTES.myRoutes} title={t(lang, "myRoutes")} text={t(lang, "status")} />
          </>
        ) : (
          <>
            <ActionCard href={APP_ROUTES.intercityRequest} title={t(lang, "createRequest")} text={t(lang, "details")} />
            <ActionCard href={APP_ROUTES.intercityOffers} title={t(lang, "availableOffers")} text={t(lang, "tabsRoutes")} />
            <ActionCard href={APP_ROUTES.myRequests} title={t(lang, "myRequests")} text={t(lang, "status")} />
          </>
        )}

        <ActionCard href={APP_ROUTES.currentTrip} title={t(lang, "currentTrip")} text={t(lang, "chat")} />
      </div>
      <BottomNav />
    </main>
  );
}
