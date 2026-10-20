import { Link } from "react-router-dom";
import { useApp } from "../hooks/AppContext";

export default function NotFound() {
  const { t } = useApp();
  return (
    <div className="py-20 text-center">
      <h1 className="text-3xl font-bold text-forest-800">404</h1>
      <p className="mt-2 text-ink-muted">Page not found.</p>
      <Link to="/" className="btn btn-primary mt-6">{t("nav_dashboard")}</Link>
    </div>
  );
}
