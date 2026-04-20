/**
 * AuthPage.jsx - Unified authentication page
 * 
 * Three modes:
 *  • signin   — sign in (any user)
 *  • register — create passenger account (with OTP verification)
 *  • setup    — create admin account (requires ADMIN_SETUP_KEY)
 *
 * The "Admin Setup" tab is hidden by default.
 * It appears only when clicking the "First-time admin setup?" link
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/SessionAuthContext';
import { useToast } from '../../context/ToastContext';
import { Button, Input, Card, Spinner, Icon } from '../../components/UI';
import OTPVerification from '../../components/OTPVerification';
import { formatEmailForDisplay } from '../../utils/emailUtils';
import api from '../../services/api';
import sessionApi from '../../services/sessionApi';

// OTP Input Component for password reset
const ResetOTPInput = ({ value, onChange, disabled, error }) => {
  const inputRefs = useRef([]);
  const [otp, setOtp] = useState(['', '', '', '', '', '']);

  useEffect(() => {
    if (value && typeof value === 'string') {
      const digits = value.split('').slice(0, 6);
      while (digits.length < 6) digits.push('');
      setOtp(digits);
    } else if (!value) {
      setOtp(['', '', '', '', '', '']);
    }
  }, [value]);

  const handleChange = (index, e) => {
    const val = e.target.value.replace(/\D/g, '');
    const newOtp = [...otp];
    newOtp[index] = val;
    setOtp(newOtp);
    if (onChange) onChange(newOtp.join(''));
    // Move focus
    if (val && index < 5 && inputRefs.current[index + 1]) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const newOtp = [...otp];
      newOtp[index - 1] = '';
      setOtp(newOtp);
      if (inputRefs.current[index - 1]) {
        inputRefs.current[index - 1].focus();
      }
      if (onChange) onChange(newOtp.join(''));
    }
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('Text').replace(/\D/g, '').slice(0, 6);
    const newOtp = pasted.split('');
    while (newOtp.length < 6) newOtp.push('');
    setOtp(newOtp);
    if (onChange) onChange(newOtp.join(''));
    // Focus last
    if (inputRefs.current[5]) inputRefs.current[5].focus();
  };

  return (
    <div style={{ display: 'flex', gap: 8, justifyContent: 'center', margin: '16px 0' }}>
      {[0, 1, 2, 3, 4, 5].map((index) => (
        <input
          key={`reset-otp-${index}`}
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
            width: 36,
            height: 44,
            fontSize: 22,
            textAlign: 'center',
            border: error ? '2px solid #ef4444' : '1px solid #cbd5e1',
            borderRadius: 8,
            background: '#fff',
            outline: 'none',
            boxShadow: error ? '0 0 0 2px #ef4444' : undefined,
          }}
        />
      ))}
	</div>
  );
};

export default function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();

  const {
    login,
    initiateRegistration,
    verifyRegistration,
    resendOtp,
    refreshUser,
  } = useAuth();

  const initialMode = (() => {
    const p = String(location.pathname || '/login');
    if (p.includes('admin-setup')) return 'setup';
    if (p.includes('forgot-password')) return 'forgot-password';
    if (p.includes('register')) return 'register';
    return 'signin';
  })();

  const [mode, setMode] = useState(initialMode);
  const [form, setForm] = useState({
    setupKey: '',
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phoneNumber: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  const [pendingEmail, setPendingEmail] = useState('');
  const [otpExpiresInMinutes, setOtpExpiresInMinutes] = useState(15);

  const [resetOtp, setResetOtp] = useState('');
  const [resetOtpSent, setResetOtpSent] = useState(false);
  const [resetOtpExpiresInMinutes, setResetOtpExpiresInMinutes] = useState(1);
  const [resetOtpTimeLeft, setResetOtpTimeLeft] = useState(0);

  const from = location.state?.from?.pathname || '/';

  useEffect(() => {
    const p = String(location.pathname || '/login');
    if (p.includes('admin-setup')) setMode('setup');
    else if (p.includes('forgot-password')) setMode('forgot-password');
    else if (p.includes('register')) setMode('register');
    else setMode((prev) => (prev === 'employee' ? 'employee' : 'signin'));
  }, [location.pathname]);

  useEffect(() => {
    const pwd = String(form.password || '');
    let score = 0;
    if (pwd.length >= 8) score += 25;
    if (/[A-Z]/.test(pwd)) score += 20;
    if (/[a-z]/.test(pwd)) score += 15;
    if (/\d/.test(pwd)) score += 20;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 20;
    setPasswordStrength(Math.min(100, score));
  }, [form.password]);

  useEffect(() => {
    if (mode !== 'reset-password' || resetOtpTimeLeft <= 0) return;
    const id = setInterval(() => {
      setResetOtpTimeLeft((v) => (v > 0 ? v - 1 : 0));
    }, 1000);
    return () => clearInterval(id);
  }, [mode, resetOtpTimeLeft]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const switchMode = (next) => {
    setErrors({});
    setLoading(false);

    if (next === 'signin') navigate('/login');
    else if (next === 'register') navigate('/register');
    else if (next === 'setup') navigate('/admin-setup');
    else if (next === 'forgot-password') navigate('/forgot-password');

    setMode(next);

    if (next === 'signin' || next === 'employee') {
      setForm((prev) => ({ ...prev, password: '', confirmPassword: '' }));
    }
  };

  const validate = () => {
    const nextErrors = {};
    const email = String(form.email || '').trim();
    const password = String(form.password || '');

    if (mode === 'signin' || mode === 'employee') {
      if (!email) nextErrors.email = 'Email is required';
      if (!password) nextErrors.password = 'Password is required';
    }

    if (mode === 'register' || mode === 'setup') {
      if (mode === 'setup' && !String(form.setupKey || '').trim()) nextErrors.setupKey = 'Setup key is required';
      if (!String(form.fullName || '').trim()) nextErrors.fullName = 'Full name is required';
      if (!email) nextErrors.email = 'Email is required';
      if (!password) nextErrors.password = 'Password is required';
      if (password && password.length < 8) nextErrors.password = 'Password must be at least 8 characters';
      if (!String(form.confirmPassword || '')) nextErrors.confirmPassword = 'Please confirm your password';
      if (password && form.confirmPassword && password !== form.confirmPassword) nextErrors.confirmPassword = 'Passwords do not match';
    }

    if (mode === 'reset-password') {
      if (!email) nextErrors.email = 'Email is required';
      if (!resetOtp || String(resetOtp).length !== 6) nextErrors.otp = 'Enter the 6-digit code';
      if (!password) nextErrors.password = 'New password is required';
      if (password && password.length < 8) nextErrors.password = 'Password must be at least 8 characters';
      if (!String(form.confirmPassword || '')) nextErrors.confirmPassword = 'Please confirm your password';
      if (password && form.confirmPassword && password !== form.confirmPassword) nextErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);

    try {
      if (mode === 'signin' || mode === 'employee') {
        const email = form.email.trim().toLowerCase();
        const password = form.password;

        let result;

        if (mode === 'employee') {
          // Staff-only login: MUST use the session client (cookies + CSRF), not the JWT api client.
          try {
            const response = await sessionApi.employeeLogin({ email, password });
            if (response?.status === 'success') {
              await refreshUser();
              const employee = response?.data?.employee || response?.data?.user;
              result = { success: true, user: employee };
            } else {
              result = { success: false, error: response?.message || 'Login failed' };
            }
          } catch (err) {
            const msg = err?.body?.message || err?.message || 'Login failed';
            result = { success: false, error: msg };
          }
        } else {
          // Passenger login (default)
          result = await login({ email, password });
        }

        if (result.success) {
          const u = result.user || {};
          toast.success(`Welcome back, ${u.fullName || u.email || u.employeeId || ''}!`);
          const role = String(u.role || u.Role || '').toUpperCase();
          const userType = String(u.type || '').toLowerCase();
          const isEmployee = userType === 'employee' || role === 'ADMIN' || role === 'EMPLOYEE';
          navigate(isEmployee ? '/admin' : from, { replace: true });
        } else {
          toast.error(result.error || 'Login failed');
          setErrors({ password: result.error || 'Login failed' });
        }

      } else if (mode === 'register') {
        // Step 1: Initiate registration with OTP
        const result = await initiateRegistration({
          fullName: form.fullName.trim(),
          email: form.email.trim().toLowerCase(),
          password: form.password,
          phoneNumber: form.phoneNumber.trim(),
        });

        if (result.success) {
          toast.success('Verification code sent to your email!');
          setPendingEmail(result.email || form.email.trim().toLowerCase());
          setOtpExpiresInMinutes(result.expiresInMinutes || 15);
          setMode('verify-otp');
        } else {
          if (result.cooldown) {
            toast.error(`Please wait ${result.cooldown} seconds before trying again`);
          } else {
            toast.error(result.error || 'Registration failed');
          }
          if (result.error?.toLowerCase().includes('email') || result.error?.toLowerCase().includes('registered')) {
            setErrors({ email: result.error });
          }
        }

      } else if (mode === 'setup') {
        // Admin setup
        const res = await api.post('/auth/setup-admin', {
          setupKey: form.setupKey.trim(),
          fullName: form.fullName.trim(),
          email: form.email.trim().toLowerCase(),
          password: form.password,
          phoneNumber: form.phoneNumber.trim(),
        });

        const data = res.data?.data || res.data;

        if (data.status === 'success' || data.accessToken) {
          toast.success('Admin account created! Please sign in.');
          switchMode('signin');
          setForm((prev) => ({ ...prev, email: form.email }));
        } else {
          toast.error(data.message || 'Setup failed');
          if (data.message?.toLowerCase().includes('key')) {
            setErrors({ setupKey: data.message });
          } else if (data.message?.toLowerCase().includes('email')) {
            setErrors({ email: data.message });
          }
        }
      }
    } catch (err) {
      const status = err.response?.status;
      const message = err.response?.data?.message || err.message || 'Something went wrong';
      
      // Handle 409 Conflict - email already exists
      if (status === 409) {
        toast.info('Admin account already exists. Please sign in.');
        switchMode('signin');
        setForm((prev) => ({ ...prev, email: form.email, password: '', confirmPassword: '' }));
        return;
      }
      
      toast.error(message);
      if (message.toLowerCase().includes('key')) {
        setErrors({ setupKey: message });
      } else if (message.toLowerCase().includes('email')) {
        setErrors({ email: message });
      }
    } finally {
      setLoading(false);
    }
  };

  // OTP Verification handlers
  const handleOtpVerify = async (otp) => {
    setLoading(true);
    try {
      // Validate email is set
      if (!pendingEmail || pendingEmail.trim() === '') {
        toast.error('Email not found. Please start registration again.');
        setMode('register');
        setPendingEmail('');
        return { success: false, error: 'Email not found' };
      }
      
      // Validate OTP
      if (!otp || otp.trim() === '') {
        toast.error('Please enter the verification code');
        return { success: false, error: 'OTP required' };
      }
      
      const result = await verifyRegistration(pendingEmail, otp);

      if (result.success) {
        toast.success('Account verified! Welcome to Smart Railway.');
        navigate(from, { replace: true });
      } else {
        // Handle specific error cases
        if (result.error_code === 'SESSION_EXPIRED') {
          toast.error('Registration session expired. Please start over.');
          setMode('register');
          setPendingEmail('');
          return result;
        } else if (result.error_code === 'OTP_EXPIRED') {
          toast.error('Verification code expired. Request a new one.');
          return result;
        } else if (result.error_code === 'NO_OTP_FOUND') {
          toast.error('No verification code found. Please restart registration.');
          setMode('register');
          setPendingEmail('');
          return result;
        } else if (result.attemptsRemaining !== undefined) {
          toast.error(`Invalid code. ${result.attemptsRemaining} attempts remaining.`);
        } else {
          toast.error(result.error || result.message || 'Verification failed');
        }
        return result;
      }
    } catch (err) {
      toast.error('Verification failed. Please try again.');
      return { success: false, error: 'Verification failed' };
    } finally {
      setLoading(false);
    }
  };

  const handleOtpResend = async () => {
    try {
      const result = await resendOtp(pendingEmail);

      if (result.success) {
        const remaining = result.remaining_resend_attempts;
        if (remaining !== undefined && remaining > 0) {
          toast.success(`New code sent! ${remaining} resend${remaining !== 1 ? 's' : ''} remaining.`);
        } else {
          toast.success('New verification code sent!');
        }
        setOtpExpiresInMinutes(result.expiresInMinutes || 15);
      } else {
        if (result.limit_exceeded) {
          toast.error(result.error || 'Maximum resend limit reached. Please try again later.');
        } else if (result.cooldown) {
          toast.error(`Please wait ${result.cooldown} seconds before resending`);
        } else {
          toast.error(result.error || 'Failed to resend code');
        }
      }
      return result;
    } catch (err) {
      toast.error('Failed to resend code');
      return { success: false, error: 'Failed to resend' };
    }
  };

  const handleOtpCancel = () => {
    setPendingEmail('');
    setMode('register');
    toast.info('Registration cancelled. You can try again.');
  };

  // Forgot Password handlers
  const handleForgotPassword = async () => {
    console.log('🔑 Forgot password clicked, email:', form.email);
    
    if (!form.email) {
      setErrors({ email: 'Please enter your email address' });
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      console.log('🔑 Sending forgot password request...');
      const response = await api.post('/auth/forgot-password', {
        email: form.email
      });

      console.log('🔑 Forgot password response:', response.data);

      if (response.data.status === 'success') {
        const maskedEmail = formatEmailForDisplay(form.email, 'confirmation');
        toast.success(`Verification code sent to ${maskedEmail}`);
        setResetOtpSent(true);
        
        // Set timer from response
        const expiresInMinutes = response.data.expiresInMinutes || 1;
        setResetOtpExpiresInMinutes(expiresInMinutes);
        setResetOtpTimeLeft(expiresInMinutes * 60); // Convert to seconds
        
        setMode('reset-password');
      } else {
        if (response.data.cooldown) {
          toast.error(`Please wait ${response.data.cooldown} seconds before requesting another code`);
        } else {
          toast.error(response.data.message || 'Failed to send verification code');
        }
      }
    } catch (error) {
      console.error('🔑 Forgot password error:', error);
      const status = error.response?.status;
      const errorMsg = error.response?.data?.message || 'Failed to send verification code';
      
      if (status === 404) {
        // Handle user not found case
        toast.error(errorMsg);
        setErrors({ email: 'This email is not registered' });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (otp = resetOtp) => {
    const newErrors = {};

    if (!form.email) newErrors.email = 'Email is required';
    if (!otp || otp.length !== 6) newErrors.otp = 'Please enter the 6-digit verification code';
    if (!form.password) newErrors.password = 'New password is required';
    if (form.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (form.password !== form.confirmPassword) newErrors.confirmPassword = 'Passwords do not match';

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const response = await api.post('/auth/reset-password', {
        email: form.email,
        otp: otp,
        newPassword: form.password
      });

      if (response.data.status === 'success') {
        toast.success('Password reset successfully! Please sign in with your new password.');
        setForm(prev => ({ ...prev, password: '', confirmPassword: '' }));
        setResetOtp('');
        setResetOtpSent(false);
        navigate('/login');
      } else {
        toast.error(response.data.message || 'Password reset failed');
      }
    } catch (error) {
      console.error('Reset password error:', error);
      const errorMsg = error.response?.data?.message || 'Password reset failed';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleResendResetOtp = async () => {
    setLoading(true);
    try {
      const response = await api.post('/auth/forgot-password', {
        email: form.email
      });

      if (response.data.status === 'success') {
        const remaining = response.data.remaining_resend_attempts;
        if (remaining !== undefined && remaining > 0) {
          toast.success(`New code sent! ${remaining} resend${remaining !== 1 ? 's' : ''} remaining.`);
        } else {
          toast.success('New verification code sent!');
        }
        
        // Reset timer
        const expiresInMinutes = response.data.expiresInMinutes || 1;
        setResetOtpExpiresInMinutes(expiresInMinutes);
        setResetOtpTimeLeft(expiresInMinutes * 60);
      } else {
        if (response.data.limit_exceeded) {
          toast.error(response.data.message || 'Maximum resend limit reached. Please try again later.');
        } else if (response.data.cooldown) {
          toast.error(`Please wait ${response.data.cooldown} seconds before resending`);
        } else {
          toast.error(response.data.message || 'Failed to resend code');
        }
      }
    } catch (error) {
      console.error('Resend OTP error:', error);
      const status = error.response?.status;
      const errorMsg = error.response?.data?.message || 'Failed to resend verification code';
      const limit_exceeded = error.response?.data?.limit_exceeded;
      
      if (limit_exceeded) {
        toast.error(errorMsg);
      } else if (status === 404) {
        // Handle user not found case - redirect back to forgot password
        toast.error(errorMsg);
        setMode('forgot-password');
        setErrors({ email: 'This email is not registered' });
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setResetOtp('');
    setResetOtpSent(false);
    setErrors({});
    navigate('/login');
  };

  const isSetup = mode === 'setup';
  const isOtpMode = mode === 'verify-otp';
  const isForgotMode = mode === 'forgot-password';
  const isResetMode = mode === 'reset-password';
  const accentColor = isSetup ? '#ef4444' : '#3b82f6';
  const gradientBg = isSetup
    ? 'linear-gradient(135deg, #ef4444, #dc2626)'
    : 'linear-gradient(135deg, #3b82f6, #8b5cf6)';

  // Tabs for main modes (Sign In, Employee, Register)
  const tabs = isSetup
    ? [
        { key: 'signin', label: 'Sign In' },
        { key: 'setup', label: '🔑 Admin Setup' },
      ]
    : [
        { key: 'signin', label: 'Sign In' },
        { key: 'employee', label: 'Employee' },
        { key: 'register', label: 'Register' },
      ];

  const getStrengthColor = () => {
    if (passwordStrength < 33) return '#ef4444';
    if (passwordStrength < 66) return '#f59e0b';
    return '#22c55e';
  };

  const getStrengthLabel = () => {
    if (passwordStrength < 33) return 'Weak';
    if (passwordStrength < 66) return 'Medium';
    return 'Strong';
  };

  // Render forgot password screen
  if (isForgotMode) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
          background: 'linear-gradient(135deg, var(--bg-base) 0%, #0a1628 100%)',
          fontFamily: 'var(--font-body)',
        }}
      >
        <Card
          style={{
            maxWidth: 440,
            width: '100%',
            padding: 32,
            background: 'rgba(30, 41, 59, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div
              style={{
                width: 60,
                height: 60,
                borderRadius: 16,
                background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                fontSize: 28,
              }}
            >
              🔑
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              Forgot Password
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Enter your email and we'll send you a verification code
            </p>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleForgotPassword();
            }}
            style={{ display: 'flex', flexDirection: 'column', gap: 16 }}
          >
            <Input
              label="Email Address"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="your@email.com"
              error={errors.email}
              required
            />

            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              style={{ width: '100%', marginTop: 8, justifyContent: 'center', padding: '14px 24px' }}
            >
              {loading ? <Spinner size={20} color="#fff" /> : 'Send Verification Code'}
            </Button>

            <button
              type="button"
              onClick={handleBackToLogin}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: 14,
                cursor: 'pointer',
                marginTop: 8,
                textDecoration: 'underline',
              }}
            >
              Back to Sign In
            </button>
          </form>
        </Card>
      </div>
    );
  }

  // Render OTP verification screen
  if (isOtpMode) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 24,
          background: 'linear-gradient(135deg, var(--bg-base) 0%, #0a1628 100%)',
          fontFamily: 'var(--font-body)',
        }}
      >
        {/* Background effects */}
        <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
          <div
            style={{
              position: 'absolute',
              top: -150,
              right: -150,
              width: 400,
              height: 400,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(59,130,246,0.1), transparent)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: -100,
              left: -100,
              width: 300,
              height: 300,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(139,92,246,0.1), transparent)',
            }}
          />
        </div>

        <Card
          style={{
            maxWidth: 440,
            width: '100%',
            padding: 32,
            position: 'relative',
            zIndex: 1,
            background: 'rgba(30, 41, 59, 0.95)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div
              style={{
                width: 60,
                height: 60,
                borderRadius: 16,
                background: gradientBg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 16px',
                fontSize: 28,
              }}
            >
              ✉️
            </div>
            <h1
              style={{
                fontSize: 24,
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: 8,
              }}
            >
              Verify Your Email
            </h1>
            <p
              style={{
                color: 'var(--text-secondary)',
                fontSize: 14,
              }}
            >
              We've sent a verification code to<br />
              <strong style={{ color: accentColor }}>{formatEmailForDisplay(pendingEmail, 'confirmation')}</strong>
            </p>
          </div>

          {/* OTP Verification Component */}
          <OTPVerification
            email={pendingEmail}
            onVerify={handleOtpVerify}
            onResend={handleOtpResend}
            onBack={handleOtpCancel}
            expiresInMinutes={otpExpiresInMinutes}
            loading={loading}
          />
        </Card>
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        background: 'linear-gradient(135deg, var(--bg-base) 0%, #0a1628 100%)',
        fontFamily: 'var(--font-body)',
      }}
    >
      {/* Background effects */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
        <div
          style={{
            position: 'absolute',
            top: '20%',
            left: '30%',
            width: 500,
            height: 500,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${isSetup ? 'rgba(239,68,68,0.06)' : 'rgba(59,130,246,0.06)'} 0%, transparent 70%)`,
            filter: 'blur(40px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '20%',
            right: '25%',
            width: 400,
            height: 400,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 70%)',
            filter: 'blur(40px)',
          }}
        />
      </div>

      <div style={{ width: '100%', maxWidth: 420, position: 'relative', zIndex: 1 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              background: gradientBg,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 14px',
              boxShadow: `0 8px 32px ${accentColor}55`,
            }}
          >
            <Icon name="train" size={26} style={{ color: '#fff' }} />
          </div>
          <h1
            style={{
              margin: '0 0 4px',
              fontSize: 24,
              fontWeight: 800,
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-display)',
            }}
          >
            Smart Railway
          </h1>
          <p style={{ margin: 0, fontSize: 13, color: 'var(--text-muted)' }}>
            {mode === 'signin' || mode === 'employee'
              ? 'Sign in to your account'
              : mode === 'register'
              ? 'Create a passenger account'
              : 'Create or reset the admin account'}
          </p>
        </div>

        {/* Card */}
        <Card
          style={{
            background: 'var(--bg-elevated)',
            border: `1px solid ${isSetup ? '#3f1717' : 'var(--border)'}`,
            borderRadius: 20,
            padding: 32,
          }}
        >
          {/* Tabs */}
          <div
            style={{
              display: 'flex',
              background: 'var(--bg-base)',
              border: '1px solid var(--border)',
              borderRadius: 12,
              padding: 4,
              marginBottom: 28,
            }}
          >
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => switchMode(tab.key)}
                style={{
                  flex: 1,
                  padding: '9px 0',
                  borderRadius: 9,
                  border: 'none',
                  background: mode === tab.key ? gradientBg : 'transparent',
                  color: mode === tab.key ? '#fff' : 'var(--text-muted)',
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Setup Key (only for admin setup) */}
              {mode === 'setup' && (
                <Input
                  label="Setup Key"
                  name="setupKey"
                  type="password"
                  value={form.setupKey}
                  onChange={handleChange}
                  placeholder="Enter the admin setup key"
                  error={errors.setupKey}
                  required
                />
              )}

              {/* Full Name (register and setup) */}
              {(mode === 'register' || mode === 'setup') && (
                <Input
                  label="Full Name"
                  name="fullName"
                  type="text"
                  value={form.fullName}
                  onChange={handleChange}
                  placeholder={mode === 'setup' ? 'Admin Name' : 'Your full name'}
                  error={errors.fullName}
                  required
                />
              )}

              {/* Email */}
              <Input
                label="Email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                placeholder={mode === 'setup' ? 'admin@admin.com' : 'your@email.com'}
                error={errors.email}
                required
              />

              {/* Password */}
              <div>
                <Input
                  label="Password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  error={errors.password}
                  required
                />
                {/* Password strength (register/setup only) */}
                {(mode === 'register' || mode === 'setup') && form.password && (
                  <div style={{ marginTop: 8 }}>
                    <div
                      style={{
                        height: 4,
                        background: 'var(--bg-base)',
                        borderRadius: 2,
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          height: '100%',
                          width: `${passwordStrength}%`,
                          background: getStrengthColor(),
                          transition: 'width 0.3s, background 0.3s',
                        }}
                      />
                    </div>
                    <span style={{ fontSize: 11, color: getStrengthColor(), marginTop: 4, display: 'block' }}>
                      Password strength: {getStrengthLabel()}
                    </span>
                  </div>
                )}
              </div>

              {/* Confirm Password (register and setup) */}
              {(mode === 'register' || mode === 'setup') && (
                <Input
                  label="Confirm Password"
                  name="confirmPassword"
                  type={showPassword ? 'text' : 'password'}
                  value={form.confirmPassword}
                  onChange={handleChange}
                  placeholder="••••••••"
                  error={errors.confirmPassword}
                  required
                />
              )}

              {/* Phone Number (register and setup) */}
              {(mode === 'register' || mode === 'setup') && (
                <Input
                  label="Phone Number (Optional)"
                  name="phoneNumber"
                  type="tel"
                  value={form.phoneNumber}
                  onChange={handleChange}
                  placeholder="+1234567890"
                  error={errors.phoneNumber}
                />
              )}

              {/* Show/hide password toggle */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--text-muted)',
                    fontSize: 12,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <Icon name={showPassword ? 'eye-off' : 'eye'} size={14} />
                  {showPassword ? 'Hide' : 'Show'} password
                </button>
                {(mode === 'signin' || mode === 'employee') && (
                  <button
                    type="button"
                    onClick={() => navigate('/forgot-password')}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--accent-blue)',
                      fontSize: 12,
                      fontWeight: 500,
                      textDecoration: 'none',
                      cursor: 'pointer',
                    }}
                  >
                    Forgot password?
                  </button>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              style={{
                width: '100%',
                marginTop: 24,
                justifyContent: 'center',
                padding: '14px 24px',
                background: isSetup ? gradientBg : undefined,
              }}
            >
              {loading ? (
                <Spinner size={20} color="#fff" />
              ) : mode === 'signin' || mode === 'employee' ? (
                'Sign In'
              ) : mode === 'register' ? (
                'Create Account'
              ) : (
                'Setup Admin'
              )}
            </Button>
          </form>

          {/* Footer links */}
          <div
            style={{
              marginTop: 24,
              paddingTop: 24,
              borderTop: '1px solid var(--border)',
              textAlign: 'center',
            }}
          >
            {mode === 'signin' && !isSetup && (
              <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: 0 }}>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => switchMode('register')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-blue)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  Create one
                </button>
              </p>
            )}
            {mode === 'register' && (
              <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: 0 }}>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => switchMode('signin')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-blue)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  Sign in
                </button>
              </p>
            )}
            {mode === 'setup' && (
              <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: 0 }}>
                <button
                  type="button"
                  onClick={() => switchMode('signin')}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--accent-blue)',
                    fontWeight: 600,
                    cursor: 'pointer',
                    padding: 0,
                  }}
                >
                  ← Back to Sign In
                </button>
              </p>
            )}
          </div>
        </Card>

        {/* Admin setup link (hidden by default) */}
        {/* {mode !== 'setup' && (
          <div style={{ marginTop: 24, textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => switchMode('setup')}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: 12,
                cursor: 'pointer',
                opacity: 0.6,
                transition: 'opacity 0.2s',
              }}
              onMouseOver={(e) => (e.target.style.opacity = 1)}
              onMouseOut={(e) => (e.target.style.opacity = 0.6)}
            >
              First-time admin setup?
            </button>
          </div>
        )} */}

        {/* Admin setup info */}
        {mode === 'setup' && (
          <div
            style={{
              marginTop: 16,
              padding: 16,
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 12,
            }}
          >
            <p style={{ fontSize: 12, color: '#f87171', margin: 0 }}>
              <strong>Note:</strong> Contact your system administrator for the setup key.
              <br />
              Admin emails must end with <code style={{ background: 'rgba(239, 68, 68, 0.2)', padding: '2px 6px', borderRadius: 4 }}>@admin.com</code>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
