import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { STRINGS } from "../i18n/strings";
import { api } from "../services/api";

const AppContext = createContext(null);

// localStorage can throw (private mode, blocked storage) — never let that break the app
const storage = {
  get(key) {
    try { return localStorage.getItem(key); } catch { return null; }
  },
  set(key, value) {
    try { value == null ? localStorage.removeItem(key) : localStorage.setItem(key, value); } catch { /* ignore */ }
  },
};

export function AppProvider({ children }) {
  const [lang, setLangState] = useState(() => storage.get("kv_lang") || "en");
  const [farmerId, setFarmerIdState] = useState(() => Number(storage.get("kv_farmer_id")) || null);
  const [farmer, setFarmer] = useState(null);
  const [farmerLoading, setFarmerLoading] = useState(Boolean(farmerId));

  const setLang = useCallback((l) => { setLangState(l); storage.set("kv_lang", l); }, []);
  const setFarmerId = useCallback((id) => { setFarmerIdState(id); storage.set("kv_farmer_id", id ? String(id) : null); }, []);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);

  const refreshFarmer = useCallback(async () => {
    if (!farmerId) { setFarmer(null); setFarmerLoading(false); return; }
    setFarmerLoading(true);
    try {
      setFarmer(await api.getFarmer(farmerId));
    } catch (e) {
      if (e.status === 404) setFarmerId(null); // profile was deleted on the server
      setFarmer(null);
    } finally {
      setFarmerLoading(false);
    }
  }, [farmerId, setFarmerId]);

  useEffect(() => { refreshFarmer(); }, [refreshFarmer]);

  const t = useCallback((key) => STRINGS[lang]?.[key] ?? STRINGS.en[key] ?? key, [lang]);

  const value = useMemo(() => ({
    lang, setLang, t, farmerId, setFarmerId, farmer, setFarmer, farmerLoading, refreshFarmer,
    farm: farmer?.farms?.[0] || null,
  }), [lang, setLang, t, farmerId, setFarmerId, farmer, farmerLoading, refreshFarmer]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside <AppProvider>");
  return ctx;
}
