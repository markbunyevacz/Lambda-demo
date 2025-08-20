/**
 * ============================================================================
 * ERROR HANDLING UTILITIES
 * ============================================================================
 * 
 * Centralized error handling for the frontend application
 */

import { ApiError, NetworkError, ValidationError, AuthenticationError, NotFoundError } from './api';

// ============================================================================
// ERROR MESSAGES
// ============================================================================

const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  'network_error': 'Hálózati hiba történt. Kérjük, ellenőrizze az internetkapcsolatát.',
  'timeout': 'A kérés időtúllépés miatt megszakadt. Kérjük, próbálja újra.',
  'server_unavailable': 'A szerver jelenleg nem elérhető. Kérjük, próbálja újra később.',
  
  // Authentication errors
  'unauthorized': 'Nincs jogosultsága ehhez a művelethez.',
  'session_expired': 'A munkamenet lejárt. Kérjük, jelentkezzen be újra.',
  
  // Validation errors
  'invalid_input': 'Érvénytelen adatok. Kérjük, ellenőrizze a bevitt információkat.',
  'required_field': 'Ez a mező kötelező.',
  'invalid_format': 'Érvénytelen formátum.',
  
  // Resource errors
  'not_found': 'A keresett elem nem található.',
  'already_exists': 'Ez az elem már létezik.',
  
  // Generic errors
  'unknown_error': 'Ismeretlen hiba történt. Kérjük, próbálja újra.',
  'operation_failed': 'A művelet sikertelen volt.',
};

// ============================================================================
// ERROR SEVERITY LEVELS
// ============================================================================

export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

// ============================================================================
// ERROR CONTEXT
// ============================================================================

export interface ErrorContext {
  operation?: string;
  component?: string;
  userId?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// FORMATTED ERROR
// ============================================================================

export interface FormattedError {
  title: string;
  message: string;
  severity: ErrorSeverity;
  code?: string;
  details?: any;
  actions?: ErrorAction[];
  context?: ErrorContext;
}

export interface ErrorAction {
  label: string;
  action: () => void;
  primary?: boolean;
}

// ============================================================================
// ERROR HANDLER CLASS
// ============================================================================

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorListeners: Array<(error: FormattedError) => void> = [];
  private errorLog: FormattedError[] = [];
  private maxLogSize = 100;

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * Handle an error and format it for display
   */
  handle(error: Error | ApiError, context?: ErrorContext): FormattedError {
    const formattedError = this.formatError(error, context);
    
    // Log the error
    this.logError(formattedError);
    
    // Notify listeners
    this.notifyListeners(formattedError);
    
    // Report to monitoring service (if configured)
    this.reportError(formattedError);
    
    return formattedError;
  }

  /**
   * Format an error for display
   */
  private formatError(error: Error | ApiError, context?: ErrorContext): FormattedError {
    let title = 'Hiba';
    let message = error.message;
    let severity = ErrorSeverity.ERROR;
    let code: string | undefined;
    let details: any;
    let actions: ErrorAction[] = [];

    // Handle specific error types
    if (error instanceof NetworkError) {
      title = 'Kapcsolati hiba';
      message = ERROR_MESSAGES.network_error;
      severity = ErrorSeverity.WARNING;
      actions = [
        {
          label: 'Újrapróbálkozás',
          action: () => window.location.reload(),
          primary: true,
        },
      ];
    } else if (error instanceof ValidationError) {
      title = 'Érvénytelen adatok';
      message = ERROR_MESSAGES.invalid_input;
      severity = ErrorSeverity.WARNING;
      details = error.details;
    } else if (error instanceof AuthenticationError) {
      title = 'Hitelesítési hiba';
      message = ERROR_MESSAGES.unauthorized;
      severity = ErrorSeverity.ERROR;
      actions = [
        {
          label: 'Bejelentkezés',
          action: () => {
            // Navigate to login
            window.location.href = '/login';
          },
          primary: true,
        },
      ];
    } else if (error instanceof NotFoundError) {
      title = 'Nem található';
      message = ERROR_MESSAGES.not_found;
      severity = ErrorSeverity.WARNING;
      actions = [
        {
          label: 'Vissza a főoldalra',
          action: () => {
            window.location.href = '/';
          },
          primary: true,
        },
      ];
    } else if (error instanceof ApiError) {
      // Handle generic API errors
      if (error.statusCode) {
        code = `HTTP_${error.statusCode}`;
        
        if (error.statusCode >= 500) {
          title = 'Szerver hiba';
          message = ERROR_MESSAGES.server_unavailable;
          severity = ErrorSeverity.CRITICAL;
        } else if (error.statusCode === 408) {
          title = 'Időtúllépés';
          message = ERROR_MESSAGES.timeout;
          severity = ErrorSeverity.WARNING;
        }
      }
      
      details = error.details;
    }

    // Add retry action for transient errors
    if (severity === ErrorSeverity.WARNING || severity === ErrorSeverity.ERROR) {
      if (!actions.find(a => a.label === 'Újrapróbálkozás')) {
        actions.push({
          label: 'Bezárás',
          action: () => {}, // Will be handled by UI
        });
      }
    }

    return {
      title,
      message,
      severity,
      code,
      details,
      actions,
      context: {
        ...context,
        timestamp: new Date().toISOString(),
      },
    };
  }

  /**
   * Log error to internal log
   */
  private logError(error: FormattedError): void {
    this.errorLog.push(error);
    
    // Maintain max log size
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog.shift();
    }

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[Error Handler]', error);
    }
  }

  /**
   * Notify error listeners
   */
  private notifyListeners(error: FormattedError): void {
    this.errorListeners.forEach(listener => {
      try {
        listener(error);
      } catch (e) {
        console.error('Error in error listener:', e);
      }
    });
  }

  /**
   * Report error to monitoring service
   */
  private reportError(error: FormattedError): void {
    // Only report critical errors in production
    if (process.env.NODE_ENV === 'production' && error.severity === ErrorSeverity.CRITICAL) {
      // TODO: Implement error reporting to monitoring service
      // e.g., Sentry, LogRocket, etc.
    }
  }

  /**
   * Subscribe to error events
   */
  subscribe(listener: (error: FormattedError) => void): () => void {
    this.errorListeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      const index = this.errorListeners.indexOf(listener);
      if (index > -1) {
        this.errorListeners.splice(index, 1);
      }
    };
  }

  /**
   * Get error log
   */
  getErrorLog(): FormattedError[] {
    return [...this.errorLog];
  }

  /**
   * Clear error log
   */
  clearErrorLog(): void {
    this.errorLog = [];
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(error: Error | ApiError): string {
    if (error instanceof NetworkError) {
      return ERROR_MESSAGES.network_error;
    } else if (error instanceof ValidationError) {
      return ERROR_MESSAGES.invalid_input;
    } else if (error instanceof AuthenticationError) {
      return ERROR_MESSAGES.unauthorized;
    } else if (error instanceof NotFoundError) {
      return ERROR_MESSAGES.not_found;
    } else if (error instanceof ApiError) {
      if (error.statusCode && error.statusCode >= 500) {
        return ERROR_MESSAGES.server_unavailable;
      } else if (error.statusCode === 408) {
        return ERROR_MESSAGES.timeout;
      }
    }
    
    return ERROR_MESSAGES.unknown_error;
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

export const errorHandler = ErrorHandler.getInstance();

// ============================================================================
// REACT HOOKS
// ============================================================================

import { useEffect, useState } from 'react';

/**
 * React hook for error handling
 */
export function useErrorHandler() {
  const [errors, setErrors] = useState<FormattedError[]>([]);

  useEffect(() => {
    const unsubscribe = errorHandler.subscribe((error) => {
      setErrors(prev => [...prev, error]);
    });

    return unsubscribe;
  }, []);

  const clearError = (index: number) => {
    setErrors(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllErrors = () => {
    setErrors([]);
  };

  return {
    errors,
    clearError,
    clearAllErrors,
    handleError: (error: Error | ApiError, context?: ErrorContext) => 
      errorHandler.handle(error, context),
  };
}

/**
 * React hook for async error handling
 */
export function useAsyncError() {
  return (error: Error | ApiError) => {
    errorHandler.handle(error);
  };
}

// ============================================================================
// ERROR BOUNDARY HELPER
// ============================================================================

export function handleErrorBoundary(error: Error, errorInfo: any): void {
  errorHandler.handle(error, {
    component: errorInfo?.componentStack,
    metadata: { errorInfo },
  });
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Wrap an async function with error handling
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  context?: ErrorContext
): T {
  return (async (...args: Parameters<T>) => {
    try {
      return await fn(...args);
    } catch (error) {
      errorHandler.handle(error as Error, context);
      throw error;
    }
  }) as T;
}

/**
 * Create a safe async handler for event handlers
 */
export function createSafeHandler<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  context?: ErrorContext
): (...args: Parameters<T>) => Promise<void> {
  return async (...args: Parameters<T>) => {
    try {
      await fn(...args);
    } catch (error) {
      errorHandler.handle(error as Error, context);
    }
  };
}