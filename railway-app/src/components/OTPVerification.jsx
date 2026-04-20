/**
 * OTPVerification Component - Smart Railway Ticketing System
 * 
 * A reusable 6-digit OTP input component with:
 * - Auto-focus and auto-advance
 * - Paste support
 * - Timer countdown
 * - Resend functionality
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { formatEmailForDisplay } from '../utils/emailUtils';

const OTPInput = ({ value, onChange, disabled, error }) => {
  const inputRefs = useRef([]);
  // Always initialize with exactly 6 empty strings
  const [otp, setOtp] = useState(['', '', '', '', '', '']);

  // Sync with external value prop
  useEffect(() => {
    if (value && typeof value === 'string') {
      const digits = value.split('').slice(0, 6);
      // Pad with empty strings to always have 6 elements
      while (digits.length < 6) digits.push('');
      setOtp(digits);
    } else if (!value) {
      setOtp(['', '', '', '', '', '']);
    }
  }, [value]);

  const handleChange = (index, e) => {
    const val = e.target.value;
    
    // Handle multiple characters (some mobile keyboards)
    if (val.length > 1) {
      // Take only digits and distribute across boxes
      const digits = val.replace(/\D/g, '').split('').slice(0, 6 - index);
      if (digits.length > 0) {
        const newOtp = [...otp];
        digits.forEach((digit, i) => {
          if (index + i < 6) {
            newOtp[index + i] = digit;
          }
        });
        setOtp(newOtp);
        onChange(newOtp.join(''));
        
        // Focus appropriate next input
        const nextIndex = Math.min(index + digits.length, 5);
        inputRefs.current[nextIndex]?.focus();
      }
      return;
    }
    
    // Only allow single digit
    if (val && !/^\d$/.test(val)) return;

    const newOtp = [...otp];
    newOtp[index] = val;
    setOtp(newOtp);
    onChange(newOtp.join(''));

    // Auto-focus next input
    if (val && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    // Handle backspace
    if (e.key === 'Backspace') {
      if (!otp[index] && index > 0) {
        // If current box is empty, go back and clear previous
        const newOtp = [...otp];
        newOtp[index - 1] = '';
        setOtp(newOtp);
        onChange(newOtp.join(''));
        inputRefs.current[index - 1]?.focus();
      }
    }
    
    // Handle left/right arrows
    if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault();
      inputRefs.current[index - 1]?.focus();
    }
    if (e.key === 'ArrowRight' && index < 5) {
      e.preventDefault();
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    
    if (pasteData.length > 0) {
      const newOtp = pasteData.split('');
      // Pad with empty strings
      while (newOtp.length < 6) newOtp.push('');
      setOtp(newOtp);
      onChange(newOtp.slice(0, 6).join(''));
      
      // Focus last filled input or first empty
      const lastFilledIndex = Math.min(pasteData.length - 1, 5);
      inputRefs.current[lastFilledIndex]?.focus();
    }
  };

  // Always render exactly 6 boxes
  const boxes = [0, 1, 2, 3, 4, 5];

  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      justifyContent: 'center',
      flexWrap: 'nowrap',
    }}>
      {boxes.map((index) => (
        <input
          key={`otp-box-${index}`}
          ref={el => inputRefs.current[index] = el}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={otp[index] || ''}
          onChange={(e) => handleChange(index, e)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          disabled={disabled}
          autoFocus={index === 0}
          autoComplete="one-time-code"
          aria-label={`Digit ${index + 1} of 6`}
          style={{
            width: '48px',
            height: '56px',
            minWidth: '48px',
            fontSize: '24px',
            fontWeight: '600',
            fontFamily: 'monospace',
            textAlign: 'center',
            border: `2px solid ${error ? '#ef4444' : otp[index] ? '#22c55e' : '#e5e7eb'}`,
            borderRadius: '12px',
            outline: 'none',
            background: disabled ? '#f3f4f6' : 'white',
            color: '#1f2937',
            transition: 'all 0.2s ease',
            flexShrink: 0,
          }}
          onFocus={(e) => {
            e.target.style.borderColor = '#3b82f6';
            e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
            // Select text on focus for easy replacement
            e.target.select();
          }}
          onBlur={(e) => {
            e.target.style.borderColor = error ? '#ef4444' : otp[index] ? '#22c55e' : '#e5e7eb';
            e.target.style.boxShadow = 'none';
          }}
        />
      ))}
    </div>
  );
};

/**
 * OTP Verification Container Component
 */
export default function OTPVerification({
  email,
  onVerify,
  onResend,
  onBack,
  expiresInMinutes = 15,
  loading = false,
  error = null,
}) {
  const [otp, setOtp] = useState('');
  const [timeLeft, setTimeLeft] = useState(expiresInMinutes * 60);
  const [canResend, setCanResend] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [resending, setResending] = useState(false);
  const [localError, setLocalError] = useState(null);
  
  // Ref to prevent duplicate verification calls
  const isVerifyingRef = useRef(false);
  const hasAutoVerifiedRef = useRef(false);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) {
      setCanResend(true);
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setCanResend(true);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  // Resend cooldown
  useEffect(() => {
    if (resendCooldown <= 0) return;

    const timer = setInterval(() => {
      setResendCooldown(prev => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [resendCooldown]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleVerify = useCallback(async () => {
    // Prevent duplicate calls
    if (isVerifyingRef.current) {
      return;
    }
    
    setLocalError(null);
    
    // Validate OTP format
    if (!otp || otp.length === 0) {
      setLocalError('Please enter a verification code');
      return;
    }
    
    if (otp.length !== 6) {
      setLocalError('Please enter exactly 6 digits');
      return;
    }
    
    if (!/^\d+$/.test(otp)) {
      setLocalError('Code must contain only digits (0-9)');
      return;
    }

    // Mark as verifying
    isVerifyingRef.current = true;
    
    try {
      await onVerify(otp);
    } finally {
      isVerifyingRef.current = false;
    }
  }, [otp, onVerify]);

  const handleResend = async () => {
    setResending(true);
    setLocalError(null);
    
    try {
      const result = await onResend();
      
      if (result.success) {
        setTimeLeft((result.expiresInMinutes || 15) * 60);
        setCanResend(false);
        setOtp('');
      } else if (result.cooldown) {
        setResendCooldown(result.cooldown);
      }
    } finally {
      setResending(false);
    }
  };

  // Auto-verify when 6 digits entered (with debouncing and duplicate prevention)
  useEffect(() => {
    // Only auto-verify once per OTP entry
    if (otp.length === 6 && !loading && !isVerifyingRef.current && !hasAutoVerifiedRef.current) {
      hasAutoVerifiedRef.current = true; // Mark that we've auto-verified this OTP
      
      const timer = setTimeout(() => {
        handleVerify();
      }, 300); // Small delay to prevent rapid re-triggers
      
      return () => clearTimeout(timer);
    }
    
    // Reset auto-verify flag when OTP changes (user editing)
    if (otp.length < 6) {
      hasAutoVerifiedRef.current = false;
    }
  }, [otp.length, loading, handleVerify]);

  const displayError = error || localError;

  return (
    <div style={{
      maxWidth: '400px',
      margin: '0 auto',
      padding: '32px 24px',
      textAlign: 'center',
    }}>
      {/* Email Icon */}
      <div style={{
        width: '64px',
        height: '64px',
        margin: '0 auto 24px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
          <polyline points="22,6 12,13 2,6"/>
        </svg>
      </div>

      {/* Title */}
      <h2 style={{
        fontSize: '24px',
        fontWeight: '700',
        color: '#1f2937',
        margin: '0 0 8px',
      }}>
        Verify Your Email
      </h2>

      {/* Email display */}
      <p style={{
        color: '#6b7280',
        margin: '0 0 24px',
        fontSize: '14px',
      }}>
        We've sent a 6-digit code to<br />
        <strong style={{ color: '#1f2937' }}>{formatEmailForDisplay(email, 'confirmation')}</strong>
      </p>

      {/* Timer */}
      {timeLeft > 0 && (
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '8px 16px',
          background: timeLeft < 60 ? '#fef2f2' : '#f0fdf4',
          borderRadius: '20px',
          marginBottom: '24px',
          fontSize: '14px',
          color: timeLeft < 60 ? '#dc2626' : '#16a34a',
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          Code expires in {formatTime(timeLeft)}
        </div>
      )}

      {timeLeft === 0 && (
        <div style={{
          padding: '8px 16px',
          background: '#fef2f2',
          borderRadius: '8px',
          marginBottom: '24px',
          fontSize: '14px',
          color: '#dc2626',
        }}>
          Code expired. Please request a new one.
        </div>
      )}

      {/* OTP Input */}
      <div style={{ marginBottom: '16px' }}>
        <OTPInput
          value={otp}
          onChange={setOtp}
          disabled={loading || timeLeft === 0}
          error={!!displayError}
        />
      </div>

      {/* Error */}
      {displayError && (
        <div style={{
          padding: '12px 16px',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#dc2626',
          fontSize: '14px',
          marginBottom: '16px',
        }}>
          {displayError}
        </div>
      )}

      {/* Verify Button */}
      <button
        onClick={handleVerify}
        disabled={otp.length !== 6 || loading || timeLeft === 0}
        style={{
          width: '100%',
          padding: '14px 24px',
          fontSize: '16px',
          fontWeight: '600',
          color: 'white',
          background: otp.length === 6 && !loading && timeLeft > 0
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : '#d1d5db',
          border: 'none',
          borderRadius: '12px',
          cursor: otp.length === 6 && !loading && timeLeft > 0 ? 'pointer' : 'not-allowed',
          marginBottom: '16px',
          transition: 'all 0.2s ease',
        }}
      >
        {loading ? (
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" style={{ animation: 'spin 1s linear infinite' }}>
              <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="3" fill="none" opacity="0.3"/>
              <path d="M12 2a10 10 0 0 1 10 10" stroke="white" strokeWidth="3" fill="none" strokeLinecap="round"/>
            </svg>
            Verifying...
          </span>
        ) : (
          'Verify & Continue'
        )}
      </button>

      {/* Resend */}
      <div style={{
        fontSize: '14px',
        color: '#6b7280',
      }}>
        Didn't receive the code?{' '}
        {resendCooldown > 0 ? (
          <span style={{ color: '#9ca3af' }}>
            Resend in {resendCooldown}s
          </span>
        ) : (
          <button
            onClick={handleResend}
            disabled={resending || (!canResend && timeLeft > 0)}
            style={{
              background: 'none',
              border: 'none',
              color: canResend || timeLeft === 0 ? '#3b82f6' : '#9ca3af',
              cursor: canResend || timeLeft === 0 ? 'pointer' : 'not-allowed',
              fontWeight: '600',
              textDecoration: 'underline',
              padding: 0,
            }}
          >
            {resending ? 'Sending...' : 'Resend Code'}
          </button>
        )}
      </div>

      {/* Back button */}
      {onBack && (
        <button
          onClick={onBack}
          style={{
            marginTop: '24px',
            background: 'none',
            border: 'none',
            color: '#6b7280',
            cursor: 'pointer',
            fontSize: '14px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          Change email address
        </button>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// Export OTPInput for standalone use
export { OTPInput };
