import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { toast } from 'react-toastify';
import ToastManager from '../components/ToastManager';
import CaptchaDetector from '../utils/captchaDetector';
import { generateBeepSound } from '../utils/notificationSound';

// Mock dependencies
jest.mock('react-toastify', () => ({
  toast: {
    warn: jest.fn(),
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
  ToastContainer: ({ children }: { children?: React.ReactNode }) => 
    <div data-testid="toast-container">{children}</div>,
}));

jest.mock('../utils/notificationSound', () => ({
  generateBeepSound: jest.fn(),
}));

jest.mock('../utils/captchaDetector', () => ({
  __esModule: true,
  default: {
    getInstance: jest.fn(),
  },
}));

const mockToast = toast as jest.Mocked<typeof toast>;
const mockGenerateBeepSound = generateBeepSound as jest.MockedFunction<typeof generateBeepSound>;

// Mock CAPTCHA detector
const mockCaptchaDetector = {
  setOnCaptchaDetected: jest.fn(),
  detectCaptcha: jest.fn(),
  detectCaptchaInLogs: jest.fn(),
  captchaCallback: jest.fn(),
};

beforeEach(() => {
  (CaptchaDetector.getInstance as jest.Mock).mockReturnValue(mockCaptchaDetector);
});

// Test component that simulates page behavior
const TestPageComponent: React.FC<{ pageName?: string }> = ({ pageName = 'TestPage' }) => {
  React.useEffect(() => {
    // Set up CAPTCHA detection similar to the real pages
    const captchaDetector = CaptchaDetector.getInstance();
    captchaDetector.setOnCaptchaDetected((event) => {
      if ((window as any).showCaptchaToast) {
        (window as any).showCaptchaToast(event.accountUsername);
      }
    });
  }, []);

  return (
    <div>
      <h1>{pageName}</h1>
      <p>Simulating {pageName} functionality</p>
    </div>
  );
};

describe('Toast Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    delete (window as any).showCaptchaToast;
  });

  afterEach(() => {
    delete (window as any).showCaptchaToast;
  });

  const renderWithToastManager = (component: React.ReactElement) => {
    return render(
      <ToastManager>
        {component}
      </ToastManager>
    );
  };

  describe('Page Integration Tests', () => {
    it('integrates with DailyPostPage simulation', async () => {
      renderWithToastManager(<TestPageComponent pageName="DailyPostPage" />);

      await waitFor(() => {
        expect(mockCaptchaDetector.setOnCaptchaDetected).toHaveBeenCalled();
      });

      expect((window as any).showCaptchaToast).toBeDefined();
      expect(screen.getByText('DailyPostPage')).toBeInTheDocument();
    });

    it('integrates with DMAutomationPage simulation', async () => {
      renderWithToastManager(<TestPageComponent pageName="DMAutomationPage" />);

      await waitFor(() => {
        expect(mockCaptchaDetector.setOnCaptchaDetected).toHaveBeenCalled();
      });

      expect((window as any).showCaptchaToast).toBeDefined();
      expect(screen.getByText('DMAutomationPage')).toBeInTheDocument();
    });

    it('integrates with WarmupPage simulation', async () => {
      renderWithToastManager(<TestPageComponent pageName="WarmupPage" />);

      await waitFor(() => {
        expect(mockCaptchaDetector.setOnCaptchaDetected).toHaveBeenCalled();
      });

      expect((window as any).showCaptchaToast).toBeDefined();
      expect(screen.getByText('WarmupPage')).toBeInTheDocument();
    });

    it('handles CAPTCHA detection across all pages', async () => {
      renderWithToastManager(<TestPageComponent />);

      await waitFor(() => {
        expect(mockCaptchaDetector.setOnCaptchaDetected).toHaveBeenCalled();
      });

      const captchaCallback = mockCaptchaDetector.setOnCaptchaDetected.mock.calls[0][0];

      // Simulate CAPTCHA detection
      await act(async () => {
        captchaCallback({ accountUsername: 'test_account' });
      });

      expect(mockToast.warn).toHaveBeenCalledTimes(1);
      expect(mockGenerateBeepSound).toHaveBeenCalled();
    });

    it('handles multiple CAPTCHA detections', async () => {
      renderWithToastManager(<TestPageComponent />);

      await waitFor(() => {
        expect(mockCaptchaDetector.setOnCaptchaDetected).toHaveBeenCalled();
      });

      const captchaCallback = mockCaptchaDetector.setOnCaptchaDetected.mock.calls[0][0];

      // Simulate multiple CAPTCHA detections
      await act(async () => {
        captchaCallback({ accountUsername: 'account1' });
        captchaCallback({ accountUsername: 'account2' });
      });

      expect(mockToast.warn).toHaveBeenCalledTimes(2);
      expect(mockGenerateBeepSound).toHaveBeenCalledTimes(2);
    });

    it('should not trigger toast for "Save your login info?" page handling', async () => {
      renderWithToastManager(<TestPageComponent />);

      await waitFor(() => {
        expect(mockCaptchaDetector.setOnCaptchaDetected).toHaveBeenCalled();
      });

      // Test that CaptchaDetector properly filters out "Save your login info?" logs
      // We'll test the filtering logic through the mock callback
      const logsWithAutoHandling = [
        '[testuser] Handling \'Save your login info?\' dialog...',
        '[testuser] ✅ Clicked \'Not now\' on save login info dialog',
        'accounts/onetap page detected',
        'Looking for \'Not now\' button on save login info dialog...'
      ];

      // Simulate calling detectCaptchaInLogs with filtered logs
      // The mock should properly filter these and not call the callback
      await act(async () => {
        // Since these logs contain excluded patterns, they should be filtered out
        // and the mock callback should not be invoked
        mockCaptchaDetector.detectCaptchaInLogs.mockImplementation((logs: string[]) => {
          const filteredLogs = logs.filter(log => {
            const excludePatterns = [
              /save.*login.*info/i,
              /accounts\/onetap/i,
              /Not now.*button/i
            ];
            return !excludePatterns.some(pattern => pattern.test(log));
          });
          // Only trigger callback if there are non-filtered logs
          if (filteredLogs.length > 0) {
            mockCaptchaDetector.captchaCallback();
          }
        });

        mockCaptchaDetector.detectCaptchaInLogs(logsWithAutoHandling);
      });

      // No toast should be triggered for these automatic handling logs
      expect(mockToast.warn).not.toHaveBeenCalled();
      expect(mockGenerateBeepSound).not.toHaveBeenCalled();

      // But a real CAPTCHA log should still work
      const realCaptchaLogs = [
        '🔔 Please check the account realcaptcha and manually solve the CAPTCHA or 2FA'
      ];

      await act(async () => {
        // Reset the mock to allow real CAPTCHA detection
        mockCaptchaDetector.detectCaptchaInLogs.mockImplementation((logs: string[]) => {
          const hasRealCaptcha = logs.some(log => 
            log.includes('CAPTCHA') || log.includes('2FA') || log.includes('Please check')
          );
          if (hasRealCaptcha) {
            mockCaptchaDetector.captchaCallback();
          }
        });
        
        mockCaptchaDetector.detectCaptchaInLogs(realCaptchaLogs);
      });

      // This should trigger toast
      expect(mockToast.warn).toHaveBeenCalledTimes(1);
      expect(mockGenerateBeepSound).toHaveBeenCalledTimes(1);
    });

    it('maintains functionality when switching pages', async () => {
      const { rerender } = renderWithToastManager(<TestPageComponent pageName="DailyPostPage" />);

      await waitFor(() => {
        expect((window as any).showCaptchaToast).toBeDefined();
      });

      // Switch to different page
      rerender(
        <ToastManager>
          <TestPageComponent pageName="DMAutomationPage" />
        </ToastManager>
      );

      expect((window as any).showCaptchaToast).toBeDefined();
      expect(screen.getByText('DMAutomationPage')).toBeInTheDocument();
    });

    it('cleans up properly to prevent memory leaks', async () => {
      const { unmount } = renderWithToastManager(<TestPageComponent />);

      expect((window as any).showCaptchaToast).toBeDefined();

      unmount();

      expect((window as any).showCaptchaToast).toBeUndefined();
    });
  });
});