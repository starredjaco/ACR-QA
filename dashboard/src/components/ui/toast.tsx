import { useState, useCallback, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle, XCircle, Info } from "lucide-react";

export type ToastVariant = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
}

let _addToast: ((msg: string, variant?: ToastVariant) => void) | null = null;

export function toast(message: string, variant: ToastVariant = "info") {
  _addToast?.(message, variant);
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const add = useCallback((message: string, variant: ToastVariant = "info") => {
    const id = ++counterRef.current;
    setToasts((prev) => [...prev, { id, message, variant }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  _addToast = add;

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))} />
      ))}
    </div>
  );
}

function ToastItem({ toast: t, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  const icons: Record<ToastVariant, ReactNode> = {
    success: <CheckCircle className="h-4 w-4 text-green-600" />,
    error: <XCircle className="h-4 w-4 text-red-600" />,
    info: <Info className="h-4 w-4 text-blue-600" />,
  };
  return (
    <div
      onClick={onDismiss}
      className={cn(
        "flex cursor-pointer items-center gap-3 rounded-lg border bg-background px-4 py-3 shadow-lg text-sm max-w-sm",
        t.variant === "error" && "border-red-200",
        t.variant === "success" && "border-green-200"
      )}
    >
      {icons[t.variant]}
      <span>{t.message}</span>
    </div>
  );
}
