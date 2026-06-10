import { Link } from 'react-router-dom';
import { Sprout } from 'lucide-react';
const NotFound = () => (
  <div className="min-h-screen bg-[#0a150a] flex flex-col items-center justify-center text-center px-6">
    <div className="w-16 h-16 rounded-2xl bg-[#1a2e1a] flex items-center justify-center mb-4">
      <Sprout size={28} className="text-[#639922]" />
    </div>
    <h1 className="text-white text-4xl font-bold mb-2">404</h1>
    <p className="text-[#5a7a3a] text-sm mb-6">This page doesn't exist.</p>
    <Link to="/" className="px-5 py-2.5 rounded-lg bg-[#639922] text-white text-sm font-semibold hover:bg-[#74b028] transition-colors">
      Go Home
    </Link>
  </div>
);
export default NotFound;
