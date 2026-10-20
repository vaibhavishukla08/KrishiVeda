// components/ui/ComingSoon.jsx
// Used as placeholder for pages not built yet
import { Construction } from 'lucide-react';

const ComingSoon = ({ title, desc }) => (
  <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
    <div className="w-16 h-16 rounded-2xl bg-[#1a2e1a] border border-[#2a4a2a] flex items-center justify-center mb-4">
      <Construction size={28} className="text-[#639922]" />
    </div>
    <h2 className="text-white font-bold text-lg mb-2">{title}</h2>
    <p className="text-[#5a7a3a] text-sm max-w-sm">{desc || 'This feature is coming soon. Stay tuned!'}</p>
  </div>
);

export default ComingSoon;
