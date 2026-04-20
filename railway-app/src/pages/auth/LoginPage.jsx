import { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/SessionAuthContext';
import { useToast } from '../../context/ToastContext';
import { Button, Input, Card, Spinner, Icon } from '../../components/UI';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const toast = useToast();

  const from = location.state?.from?.pathname || '/';

  const [form, setForm] = useState({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loginType, setLoginType] = useState('user');
  const submitLabel = loginType === 'employee' ? 'Sign In as Employee' : 'Sign In as Passenger';
  const subtitleByLoginType = {
    user: 'Sign in to your Smart Railway account',
    employee: 'Employee sign in for Admin related rail users',
  };
  const modeHintByLoginType = {
    user: 'Passenger mode selected: this signs in through the normal user endpoint.',
    employee: 'Employee mode selected: this signs in through the dedicated employee endpoint.',
  };
  const footerByLoginType = {
    user: (
      <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
        Don&apos;t have an account?{' '}
        <Link
          to="/register"
          style={{
            color: 'var(--accent-blue)',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          Create one
        </Link>
      </p>
    ),
    employee: (
      <p style={{ color: 'var(--text-muted)', fontSize: 13, margin: 0 }}>
        Employee accounts are created by admin invitations.
      </p>
    ),
  };

  const normalizeError = (value) => String(value || '').toLowerCase();

  const resolveFieldErrors = (errorMessage) => {
    const normalized = normalizeError(errorMessage);
    if (normalized.includes('password')) {
      return { password: 'Invalid email or password' };
    }
    if (normalized.includes('email')) {
      return { email: errorMessage };
    }
    return { password: errorMessage };
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!form.email.trim()) {
      newErrors.email = 'Email is required';
    }

    if (!form.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    
    // Use employee-specific login method if type is employee
    const loginMethod = loginType === 'employee' ? 'employeeLogin' : 'login';
    
    const result = await login({
      email: form.email.trim().toLowerCase(),
      password: form.password,
      loginType,
      method: loginMethod // Forward the method hint
    });

    setLoading(false);

    if (result.success) {
      toast.success(`Welcome back, ${result.user.fullName}!`);
      navigate(from, { replace: true });
    } else {
      const rawError = result.error || 'Login failed';
      const rawLower = String(rawError || '').toLowerCase();

      const parsedStatus = (() => {
        const match = /Request failed \((\d+)\)/.exec(String(rawError || ''));
        return match ? Number(match[1]) : undefined;
      })();

      const status = result.status ?? parsedStatus;

      const humanizeConnectivityError = (msg) => {
        const text = String(msg || '');
        if (
          /proxy error: could not proxy request/i.test(text) ||
          /econnrefused/i.test(text) ||
          /failed to fetch/i.test(text)
        ) {
          return 'Backend server is not reachable. Start it with: catalyst serve';
        }
        return text || 'Something went wrong';
      };

      const humanized = humanizeConnectivityError(rawError);
      let toastMessage = humanized;

      if (!humanized.includes('catalyst serve')) {
        if (loginType === 'employee') {
          if (rawLower.includes('no employee account found') || rawLower.includes('not registered as an employee')) {
            toastMessage = 'This email is not registered as an employee. Please contact your admin.';
          } else if (status === 401) {
            toastMessage = 'Incorrect password. Please try again.';
          }
        } else {
          if (status === 404 || rawLower.includes('no account found')) {
            toastMessage = 'Email not registered. Please register to continue.';
          } else if (status === 401) {
            toastMessage = 'Incorrect password. Please try again.';
          }
        }

        if (status === 400 && rawLower.startsWith('request failed')) {
          toastMessage = 'Please enter a valid email and password.';
        }
      }

      toast.error(toastMessage);

      if (toastMessage.includes('catalyst serve')) {
        setErrors({ email: 'Server unavailable. Start backend (catalyst serve).' });
      } else if (loginType === 'employee' && (rawLower.includes('no employee account found') || rawLower.includes('not registered as an employee'))) {
        setErrors({ email: 'Email not registered as an employee' });
      } else if (loginType !== 'employee' && (status === 404 || rawLower.includes('no account found'))) {
        setErrors({ email: 'Email not registered' });
      } else if (status === 401 || rawLower.includes('invalid email or password') || rawLower.includes('password')) {
        setErrors({ password: 'Incorrect password' });
      } else {
        setErrors(resolveFieldErrors(rawError));
      }
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
      background: 'linear-gradient(135deg, var(--bg-base) 0%, #0a1628 100%)',
    }}>
      <div style={{ width: '100%', maxWidth: 520 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 64, height: 64, margin: '0 auto 16px',
            background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
            borderRadius: 'var(--radius-lg)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 32px rgba(59, 130, 246, 0.3)',
          }}>
            <Icon name="train" size={32} style={{ color: '#fff' }} />
          </div>
          <h1 style={{
            fontSize: 28, fontWeight: 800, color: 'var(--text-primary)',
            fontFamily: 'var(--font-display)', margin: 0,
          }}>
            Welcome Back
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 8 }}>
            {subtitleByLoginType[loginType]}
          </p>
        </div>

        <Card padding={32}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 12,
              marginBottom: 24,
            }}
          >
            <button
              type="button"
              onClick={() => setLoginType('user')}
              style={{
                border: loginType === 'user' ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: '16px 14px',
                fontWeight: 700,
                cursor: 'pointer',
                textAlign: 'center',
                background: loginType === 'user' ? 'rgba(59,130,246,0.2)' : 'var(--bg-subtle)',
                color: loginType === 'user' ? 'var(--accent-blue)' : 'var(--text-primary)',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Icon name="user" size={24} style={{ opacity: loginType === 'user' ? 1 : 0.6 }} />
              <div>
                <div style={{ fontSize: 15, fontWeight: 800 }}>Passenger</div>
                <div style={{ fontSize: 11, fontWeight: 500, opacity: 0.7 }}>Login</div>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setLoginType('employee')}
              style={{
                border: loginType === 'employee' ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                padding: '16px 14px',
                fontWeight: 700,
                cursor: 'pointer',
                textAlign: 'center',
                background: loginType === 'employee' ? 'rgba(59,130,246,0.2)' : 'var(--bg-subtle)',
                color: loginType === 'employee' ? 'var(--accent-blue)' : 'var(--text-primary)',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <Icon name="shield" size={24} style={{ opacity: loginType === 'employee' ? 1 : 0.6 }} />
              <div>
                <div style={{ fontSize: 15, fontWeight: 800 }}>Employee</div>
                <div style={{ fontSize: 11, fontWeight: 500, opacity: 0.7 }}>Login</div>
              </div>
            </button>
          </div>

          <div
            style={{
              marginBottom: 18,
              padding: '10px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px dashed var(--border)',
              color: 'var(--text-secondary)',
              fontSize: 12,
            }}
          >
            {modeHintByLoginType[loginType]}
          </div>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <Input
                label="Email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                placeholder="Enter your email"
                required
                error={errors.email}
              />

              <div>
                <Input
                  label="Password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  required
                  error={errors.password}
                />
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: 8,
                }}>
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--text-muted)', fontSize: 12,
                      display: 'flex', alignItems: 'center', gap: 4,
                    }}
                  >
                    <Icon name={showPassword ? 'x' : 'check'} size={12} />
                    {showPassword ? 'Hide' : 'Show'} password
                  </button>
                  <Link
                    to="/forgot-password"
                    style={{
                      color: 'var(--accent-blue)',
                      fontSize: 12,
                      fontWeight: 500,
                    }}
                  >
                    Forgot password?
                  </Link>
                </div>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              style={{
                width: '100%',
                marginTop: 28,
                justifyContent: 'center',
                padding: '14px 24px',
              }}
            >
              {loading ? <Spinner size={20} color="#fff" /> : submitLabel}
            </Button>
          </form>

          <div style={{
            marginTop: 24, paddingTop: 24,
            borderTop: '1px solid var(--border)',
            textAlign: 'center',
          }}>
            {footerByLoginType[loginType]}
          </div>
        </Card>

        <div style={{
          marginTop: 32,
          padding: 20,
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border)',
        }}>
          <p style={{
            fontSize: 12, color: 'var(--text-muted)',
            textAlign: 'center', margin: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}>
            <Icon name="info" size={14} />
            Your session will remain active for 7 days
          </p>
        </div>
      </div>
    </div>
  );
}
