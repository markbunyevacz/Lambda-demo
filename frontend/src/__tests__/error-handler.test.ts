/**
 * Error Handler Tests
 */

import {
  ErrorHandler,
  ErrorSeverity,
  FormattedError,
  withErrorHandling,
  createSafeHandler,
} from '../lib/error-handler';
import {
  ApiError,
  NetworkError,
  ValidationError,
  AuthenticationError,
  NotFoundError,
} from '../lib/api';

describe('ErrorHandler', () => {
  let errorHandler: ErrorHandler;

  beforeEach(() => {
    errorHandler = ErrorHandler.getInstance();
    errorHandler.clearErrorLog();
  });

  describe('error formatting', () => {
    it('should format network errors correctly', () => {
      const error = new NetworkError();
      const formatted = errorHandler.handle(error);

      expect(formatted.title).toBe('Kapcsolati hiba');
      expect(formatted.severity).toBe(ErrorSeverity.WARNING);
      expect(formatted.actions).toHaveLength(1);
      expect(formatted.actions![0].label).toBe('Újrapróbálkozás');
    });

    it('should format validation errors correctly', () => {
      const details = { fields: { email: 'Invalid email' } };
      const error = new ValidationError('Validation failed', details);
      const formatted = errorHandler.handle(error);

      expect(formatted.title).toBe('Érvénytelen adatok');
      expect(formatted.severity).toBe(ErrorSeverity.WARNING);
      expect(formatted.details).toEqual(details);
    });

    it('should format authentication errors correctly', () => {
      const error = new AuthenticationError();
      const formatted = errorHandler.handle(error);

      expect(formatted.title).toBe('Hitelesítési hiba');
      expect(formatted.severity).toBe(ErrorSeverity.ERROR);
      expect(formatted.actions).toHaveLength(1);
      expect(formatted.actions![0].label).toBe('Bejelentkezés');
    });

    it('should format not found errors correctly', () => {
      const error = new NotFoundError();
      const formatted = errorHandler.handle(error);

      expect(formatted.title).toBe('Nem található');
      expect(formatted.severity).toBe(ErrorSeverity.WARNING);
      expect(formatted.actions).toHaveLength(1);
      expect(formatted.actions![0].label).toBe('Vissza a főoldalra');
    });

    it('should format server errors correctly', () => {
      const error = new ApiError('Server error', 500);
      const formatted = errorHandler.handle(error);

      expect(formatted.title).toBe('Szerver hiba');
      expect(formatted.severity).toBe(ErrorSeverity.CRITICAL);
      expect(formatted.code).toBe('HTTP_500');
    });

    it('should format timeout errors correctly', () => {
      const error = new ApiError('Request timeout', 408);
      const formatted = errorHandler.handle(error);

      expect(formatted.title).toBe('Időtúllépés');
      expect(formatted.severity).toBe(ErrorSeverity.WARNING);
      expect(formatted.code).toBe('HTTP_408');
    });

    it('should add context to formatted errors', () => {
      const error = new Error('Test error');
      const context = {
        operation: 'fetchProducts',
        component: 'ProductList',
      };
      const formatted = errorHandler.handle(error, context);

      expect(formatted.context).toMatchObject(context);
      expect(formatted.context?.timestamp).toBeDefined();
    });
  });

  describe('error logging', () => {
    it('should log errors to internal log', () => {
      const error1 = new NetworkError();
      const error2 = new ValidationError();

      errorHandler.handle(error1);
      errorHandler.handle(error2);

      const log = errorHandler.getErrorLog();
      expect(log).toHaveLength(2);
      expect(log[0].title).toBe('Kapcsolati hiba');
      expect(log[1].title).toBe('Érvénytelen adatok');
    });

    it('should maintain max log size', () => {
      // Create more than max log size (100) errors
      for (let i = 0; i < 105; i++) {
        errorHandler.handle(new Error(`Error ${i}`));
      }

      const log = errorHandler.getErrorLog();
      expect(log).toHaveLength(100);
      expect(log[0].message).toBe('Error 5'); // First 5 should be removed
    });

    it('should clear error log', () => {
      errorHandler.handle(new Error('Test error'));
      expect(errorHandler.getErrorLog()).toHaveLength(1);

      errorHandler.clearErrorLog();
      expect(errorHandler.getErrorLog()).toHaveLength(0);
    });
  });

  describe('error listeners', () => {
    it('should notify listeners when error occurs', () => {
      const listener = jest.fn();
      const unsubscribe = errorHandler.subscribe(listener);

      const error = new NetworkError();
      errorHandler.handle(error);

      expect(listener).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Kapcsolati hiba',
          severity: ErrorSeverity.WARNING,
        })
      );

      unsubscribe();
    });

    it('should handle multiple listeners', () => {
      const listener1 = jest.fn();
      const listener2 = jest.fn();

      errorHandler.subscribe(listener1);
      errorHandler.subscribe(listener2);

      errorHandler.handle(new Error('Test'));

      expect(listener1).toHaveBeenCalled();
      expect(listener2).toHaveBeenCalled();
    });

    it('should allow unsubscribing', () => {
      const listener = jest.fn();
      const unsubscribe = errorHandler.subscribe(listener);

      unsubscribe();
      errorHandler.handle(new Error('Test'));

      expect(listener).not.toHaveBeenCalled();
    });

    it('should handle errors in listeners gracefully', () => {
      const goodListener = jest.fn();
      const badListener = jest.fn(() => {
        throw new Error('Listener error');
      });

      errorHandler.subscribe(badListener);
      errorHandler.subscribe(goodListener);

      // Should not throw
      expect(() => {
        errorHandler.handle(new Error('Test'));
      }).not.toThrow();

      expect(goodListener).toHaveBeenCalled();
    });
  });

  describe('user messages', () => {
    it('should return appropriate user messages', () => {
      expect(errorHandler.getUserMessage(new NetworkError())).toContain('Hálózati hiba');
      expect(errorHandler.getUserMessage(new ValidationError())).toContain('Érvénytelen adatok');
      expect(errorHandler.getUserMessage(new AuthenticationError())).toContain('Nincs jogosultsága');
      expect(errorHandler.getUserMessage(new NotFoundError())).toContain('nem található');
      expect(errorHandler.getUserMessage(new ApiError('', 500))).toContain('szerver jelenleg nem elérhető');
      expect(errorHandler.getUserMessage(new ApiError('', 408))).toContain('időtúllépés');
      expect(errorHandler.getUserMessage(new Error('Unknown'))).toContain('Ismeretlen hiba');
    });
  });
});

describe('utility functions', () => {
  describe('withErrorHandling', () => {
    it('should wrap async function with error handling', async () => {
      const errorHandler = ErrorHandler.getInstance();
      const handleSpy = jest.spyOn(errorHandler, 'handle');

      const asyncFn = async (value: number) => {
        if (value < 0) {
          throw new Error('Negative value');
        }
        return value * 2;
      };

      const wrappedFn = withErrorHandling(asyncFn, { operation: 'multiply' });

      // Successful call
      const result = await wrappedFn(5);
      expect(result).toBe(10);
      expect(handleSpy).not.toHaveBeenCalled();

      // Error call
      await expect(wrappedFn(-1)).rejects.toThrow('Negative value');
      expect(handleSpy).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Negative value' }),
        expect.objectContaining({ operation: 'multiply' })
      );
    });
  });

  describe('createSafeHandler', () => {
    it('should create safe event handler', async () => {
      const errorHandler = ErrorHandler.getInstance();
      const handleSpy = jest.spyOn(errorHandler, 'handle');

      const asyncHandler = async (event: string) => {
        if (event === 'error') {
          throw new Error('Handler error');
        }
        return event.toUpperCase();
      };

      const safeHandler = createSafeHandler(asyncHandler, { component: 'Button' });

      // Successful call
      await safeHandler('click');
      expect(handleSpy).not.toHaveBeenCalled();

      // Error call (should not throw)
      await expect(safeHandler('error')).resolves.toBeUndefined();
      expect(handleSpy).toHaveBeenCalledWith(
        expect.objectContaining({ message: 'Handler error' }),
        expect.objectContaining({ component: 'Button' })
      );
    });
  });
});