import { Wifi, WifiOff } from "lucide-react";

export function ModeBadge() {
  const mode = import.meta.env.VITE_ACRQA_MODE ?? "online";
  const offline = mode === "offline";
  return (
    <span className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${offline ? "bg-orange-100 text-orange-700" : "bg-green-100 text-green-700"}`}>
      {offline ? <WifiOff className="h-3 w-3" /> : <Wifi className="h-3 w-3" />}
      {offline ? "OFFLINE" : "ONLINE"}
    </span>
  );
}
