'use client';

import React, { useEffect, useState } from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';
import { ErrorSeverity, FormattedError } from '../lib/error-handler';

export interface ToastProps {
  id?: string;
  title?: string;
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  onClose?: () => void;
  actions?: Array<{
    label: string;
    action: () => void;
    primary?: boolean;
  }>;
}

/**
 * Individual Toast Component
 */
export function Toast({
  id,
  title,
  message,
  type = 'info',
  duration = 5000,
  onClose,
  actions,
}: ToastProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleClose = () => {
    setIsLeaving(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, 300); // Animation duration
  };

  if (!isVisible) return null;

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    error: <AlertCircle className="w-5 h-5" />,
    warning: <AlertTriangle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  };

  const colors = {
    success: 'bg-green-50 text-green-800 border-green-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
  };

  const iconColors = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  };

  return (
    <div
      className={`
        pointer-events-auto w-full max-w-sm overflow-hidden rounded-lg border shadow-lg
        ${colors[type]}
        ${isLeaving ? 'animate-slide-out' : 'animate-slide-in'}
      `}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className={`flex-shrink-0 ${iconColors[type]}`}>
            {icons[type]}
          </div>
          <div className="ml-3 w-0 flex-1">
            {title && (
              <p className="text-sm font-medium">
                {title}
              </p>
            )}
            <p className={`text-sm ${title ? 'mt-1' : ''}`}>
              {message}
            </p>
            {actions && actions.length > 0 && (
              <div className="mt-3 flex gap-2">
                {actions.map((action, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      action.action();
                      handleClose();
                    }}
                    className={`
                      text-sm font-medium rounded-md px-2 py-1
                      ${action.primary
                        ? 'bg-white text-gray-900 hover:bg-gray-100'
                        : 'text-current hover:underline'
                      }
                    `}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="ml-4 flex flex-shrink-0">
            <button
              onClick={handleClose}
              className="inline-flex rounded-md hover:opacity-75 focus:outline-none"
            >
              <span className="sr-only">Bezárás</span>
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Toast Container Component
 */
export interface ToastContainerProps {
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
}

export function ToastContainer({ position = 'top-right' }: ToastContainerProps) {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  // This would typically be connected to a global toast manager
  // For now, we'll expose methods via window for demo purposes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).showToast = (toast: ToastProps) => {
        const id = toast.id || Date.now().toString();
        setToasts(prev => [...prev, { ...toast, id }]);
      };

      (window as any).clearToasts = () => {
        setToasts([]);
      };
    }
  }, []);

  const positionClasses = {
    'top-left': 'top-0 left-0',
    'top-center': 'top-0 left-1/2 -translate-x-1/2',
    'top-right': 'top-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2',
    'bottom-right': 'bottom-0 right-0',
  };

  return (
    <div
      className={`
        fixed z-50 pointer-events-none p-4
        ${positionClasses[position]}
      `}
      aria-live="assertive"
    >
      <div className="flex flex-col gap-2">
        {toasts.map(toast => (
          <Toast
            key={toast.id}
            {...toast}
            onClose={() => removeToast(toast.id!)}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Hook for using toast notifications
 */
export function useToast() {
  const showToast = (toast: Omit<ToastProps, 'id'>) => {
    if (typeof window !== 'undefined' && (window as any).showToast) {
      (window as any).showToast(toast);
    }
  };

  const showSuccess = (message: string, title?: string) => {
    showToast({ type: 'success', message, title });
  };

  const showError = (message: string, title?: string) => {
    showToast({ type: 'error', message, title, duration: 0 }); // Don't auto-dismiss errors
  };

  const showWarning = (message: string, title?: string) => {
    showToast({ type: 'warning', message, title });
  };

  const showInfo = (message: string, title?: string) => {
    showToast({ type: 'info', message, title });
  };

  const showFormattedError = (error: FormattedError) => {
    const type = {
      [ErrorSeverity.INFO]: 'info' as const,
      [ErrorSeverity.WARNING]: 'warning' as const,
      [ErrorSeverity.ERROR]: 'error' as const,
      [ErrorSeverity.CRITICAL]: 'error' as const,
    }[error.severity];

    showToast({
      type,
      title: error.title,
      message: error.message,
      actions: error.actions,
      duration: error.severity === ErrorSeverity.ERROR || error.severity === ErrorSeverity.CRITICAL ? 0 : 5000,
    });
  };

  const clearToasts = () => {
    if (typeof window !== 'undefined' && (window as any).clearToasts) {
      (window as any).clearToasts();
    }
  };

  return {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showFormattedError,
    clearToasts,
  };
}

// Add CSS animations (should be in global CSS file)
const animationStyles = `
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slide-out {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}

.animate-slide-out {
  animation: slide-out 0.3s ease-in;
}
`;

// Inject styles if in browser
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = animationStyles;
  document.head.appendChild(style);
}