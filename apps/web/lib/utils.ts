import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

// Tailwind class merger
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format date to readable string
export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return format(d, "MMM d, yyyy 'at' h:mm a");
}

// Format date as relative time (e.g., "2 hours ago")
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}

// Get status color for badges
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    queued: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
    validating: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
    running: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300",
    completed: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
    failed: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
    cancelled: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
  };
  return colors[status] || colors.queued;
}

// Get provider display name
export function getProviderName(provider: string): string {
  const names: Record<string, string> = {
    openai: "OpenAI",
    anthropic: "Anthropic (Claude)",
    gemini: "Google Gemini",
    deepseek: "DeepSeek",
  };
  return names[provider] || provider;
}

// Get persona display name
export function getPersonaName(persona: string): string {
  const names: Record<string, string> = {
    student: "Student",
    researcher: "Researcher",
    ml_engineer: "ML Engineer",
    data_scientist: "Data Scientist",
    ai_architect: "AI Architect",
  };
  return names[persona] || persona;
}

// Format file size
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
}

// Truncate string
export function truncate(str: string, length: number = 50): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

// Download blob as file
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
