import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function severityColor(severity: string): string {
  switch (severity?.toLowerCase()) {
    case "high":
    case "critical":
      return "text-red-600 bg-red-50 border-red-200";
    case "medium":
      return "text-yellow-700 bg-yellow-50 border-yellow-200";
    case "low":
      return "text-blue-600 bg-blue-50 border-blue-200";
    default:
      return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

export function riskColor(level: string): string {
  switch (level?.toLowerCase()) {
    case "high":
      return "text-red-600 bg-red-50";
    case "medium":
      return "text-yellow-700 bg-yellow-50";
    case "low":
      return "text-green-700 bg-green-50";
    default:
      return "text-gray-600 bg-gray-50";
  }
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function truncate(s: string, n = 80): string {
  return s && s.length > n ? s.slice(0, n) + "…" : s;
}
