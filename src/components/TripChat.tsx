"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, ChatMessage } from "@/lib/api";
import { useApp } from "@/context/AppContext";
import { t } from "@/lib/i18n";

type Props = {
  tripId: number;
  tripType?: string;
};

export default function TripChat({ tripId, tripType = "generic" }: Props) {
  const { sessionToken, lang, isReady, user } = useApp();
  const [items, setItems] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  const loadMessages = useCallback(async () => {
    if (!sessionToken || !tripId) return;
    setLoading(true);
    try {
      const data = await api.chatMessages(sessionToken, tripId, tripType);
      setItems(data.items);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [sessionToken, tripId, tripType]);

  useEffect(() => {
    if (!isReady) return;
    void loadMessages();
    const timer = window.setInterval(() => {
      void loadMessages();
    }, 4000);
    return () => window.clearInterval(timer);
  }, [isReady, loadMessages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!message.trim() || !sessionToken) return;

    try {
      await api.sendChatMessage(sessionToken, tripId, message.trim(), tripType);
      setMessage("");
      await loadMessages();
    } catch {
    }
  }

  return (
    <div className="card stack">
      <div className="card-title">{t(lang, "chat")}</div>
      <div className="chat-box">
        {loading ? (
          <div className="muted">{t(lang, "loading")}</div>
        ) : items.length === 0 ? (
          <div className="muted">{t(lang, "noData")}</div>
        ) : (
          items.map((item) => {
            const mine = item.sender_tg_id === user?.tg_id;
            return (
              <div key={item.id} className={`chat-message${mine ? " mine" : ""}`}>
                <div>{item.text}</div>
                <div className="chat-time">{item.created_at}</div>
              </div>
            );
          })
        )}
      </div>
      <form className="inline-form" onSubmit={handleSubmit}>
        <input
          className="field"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={t(lang, "messagePlaceholder")}
        />
        <button className="button-main slim" type="submit">
          {t(lang, "send")}
        </button>
      </form>
    </div>
  );
}
