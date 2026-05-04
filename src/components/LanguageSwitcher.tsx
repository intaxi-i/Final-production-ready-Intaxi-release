"use client";

import { LANGUAGE_OPTIONS } from "@/lib/constants";
import { useApp } from "@/context/AppContext";

type Props = {
  compact?: boolean;
};

export default function LanguageSwitcher({ compact = true }: Props) {
  const { lang, setLang } = useApp();

  return (
    <div className={`language-switcher${compact ? " compact" : ""}`}>
      <select
        id="lang-switcher"
        className="field language-field"
        value={lang}
        onChange={(e) => setLang(e.target.value as typeof lang)}
        aria-label="Language"
      >
        {LANGUAGE_OPTIONS.map((item) => (
          <option key={item.code} value={item.code}>
            {item.label}
          </option>
        ))}
      </select>
    </div>
  );
}