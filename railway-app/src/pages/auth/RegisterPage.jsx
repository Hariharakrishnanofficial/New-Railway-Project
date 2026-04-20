import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/SessionAuthContext';
import { useToast } from '../../context/ToastContext';
import { Button, Input, Card, Spinner, Icon } from '../../components/UI';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const toast = useToast();
  const [searchParams] = useSearchParams();

  // Check for invitation token in URL
  const invitationToken = searchParams.get('invitation');
  const isEmployeeInvitation = !!invitationToken;

  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phoneNumber: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [invitationError, setInvitationError] = useState('');
  const [regType, setRegType] = useState('user'); // 'user' or 'employee'

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!form.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    }

    if (!form.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!form.password) {
      newErrors.password = 'Password is required';
    } else if (form.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (form.password !== form.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setInvitationError('');
    
    const registrationData = {
      fullName: form.fullName.trim(),
      email: form.email.trim().toLowerCase(),
      password: form.password,
      phoneNumber: form.phoneNumber.trim(),
      type: regType, // user or employee
    };
    
    // Include invitation token if this is an employee invitation
    if (invitationToken) {
      registrationData.invitationToken = invitationToken;
    }
    
    const result = await register(registrationData);

    setLoading(false);

    if (result.success) {
      const roleValue = String(result.data?.user?.role || '').toLowerCase();
      const isEmployee = roleValue === 'employee' || roleValue === 'admin';
      const welcomeMessage = isEmployee 
        ? 'Employee registration successful! Welcome to the team.' 
        : 'Registration successful! Welcome aboard.';
      
      toast.success(welcomeMessage);
      navigate('/');
    } else {
      const rawError = result.error || 'Registration failed';
      const rawLower = String(rawError || '').toLowerCase();

      const parsedStatus = (() => {
        const match = /Request failed \((\d+)\)/.exec(String(rawError || ''));
        return match ? Number(match[1]) : undefined;
      })();

      const status = result.status ?? parsedStatus;

      // Handle invitation-specific errors
      if (rawLower.includes('invitation')) {
        setInvitationError(rawError);
        return;
      }

      if (status === 409 || rawLower.includes('already registered')) {
        toast.info('Email already registered. Please sign in.');
        navigate('/login', { replace: true });
        setErrors({ email: 'Email already registered' });
        return;
      }

      const safeMessage = rawLower.startsWith('request failed')
        ? 'Registration failed. Please check your details and try again.'
        : rawError;

      toast.error(safeMessage);

      if (rawLower.includes('full name')) {
        setErrors({ fullName: rawError });
      } else if (rawLower.includes('phone')) {
        setErrors({ phoneNumber: rawError });
      } else if (rawLower.includes('password')) {
        setErrors({ password: rawError });
      } else if (rawLower.includes('email') || rawLower.includes('registered')) {
        setErrors({ email: rawError });
      } else {
        setErrors({ email: safeMessage });
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
      <div style={{ width: '100%', maxWidth: 440 }}>
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
            {regType === 'employee' ? 'Employee registration' : 'Create Account'}
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginTop: 8 }}>
            {regType === 'employee' 
              ? 'Employee registration for Admin related rail users' 
              : 'Join Smart Railway - Book tickets seamlessly'
            }
          </p>
        </div>

        <Card padding={32}>
          {!isEmployeeInvitation && (
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
                onClick={() => setRegType('user')}
                style={{
                  border: regType === 'user' ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px 14px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                  background: regType === 'user' ? 'rgba(59,130,246,0.2)' : 'var(--bg-subtle)',
                  color: regType === 'user' ? 'var(--accent-blue)' : 'var(--text-primary)',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <Icon name="user" size={24} style={{ opacity: regType === 'user' ? 1 : 0.6 }} />
                <div>
                  <div style={{ fontSize: 15, fontWeight: 800 }}>Passenger</div>
                  <div style={{ fontSize: 11, fontWeight: 500, opacity: 0.7 }}>Sign Up</div>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setRegType('employee')}
                style={{
                  border: regType === 'employee' ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '16px 14px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                  background: regType === 'employee' ? 'rgba(59,130,246,0.2)' : 'var(--bg-subtle)',
                  color: regType === 'employee' ? 'var(--accent-blue)' : 'var(--text-primary)',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <Icon name="shield" size={24} style={{ opacity: regType === 'employee' ? 1 : 0.6 }} />
                <div>
                  <div style={{ fontSize: 15, fontWeight: 800 }}>Employee</div>
                  <div style={{ fontSize: 11, fontWeight: 500, opacity: 0.7 }}>Sign Up</div>
                </div>
              </button>
            </div>
          )}

          {/* Show invitation error if any */}
          {invitationError && (
            <div style={{
              padding: 12,
              marginBottom: 20,
              backgroundColor: 'var(--bg-danger)',
              color: 'var(--text-danger)',
              borderRadius: 'var(--radius-md)',
              fontSize: 14,
              border: '1px solid var(--border-danger)',
            }}>
              {invitationError}
            </div>
          )}

          {/* Show invitation context */}
          {isEmployeeInvitation && !invitationError && (
            <div style={{
              padding: 12,
              marginBottom: 20,
              backgroundColor: 'var(--bg-info)',
              color: 'var(--text-info)',
              borderRadius: 'var(--radius-md)',
              fontSize: 14,
              border: '1px solid var(--border-info)',
            }}>
              <Icon name="briefcase" size={16} style={{ marginRight: 8 }} />
              You've been invited to join as an employee. Please complete your registration below.
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <Input
                label="Full Name"
                name="fullName"
                value={form.fullName}
                onChange={handleChange}
                placeholder="Enter your full name"
                required
                error={errors.fullName}
                icon="users"
              />

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

              <Input
                label="Phone Number"
                name="phoneNumber"
                type="tel"
                value={form.phoneNumber}
                onChange={handleChange}
                placeholder="10-digit mobile number (optional)"
              />

              <div>
                <Input
                  label="Password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Minimum 8 characters"
                  required
                  error={errors.password}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-muted)', fontSize: 12, marginTop: 6,
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}
                >
                  <Icon name={showPassword ? 'x' : 'check'} size={12} />
                  {showPassword ? 'Hide' : 'Show'} password
                </button>
              </div>

              <Input
                label="Confirm Password"
                name="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                value={form.confirmPassword}
                onChange={handleChange}
                placeholder="Re-enter your password"
                required
                error={errors.confirmPassword}
              />
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
              {loading ? <Spinner size={20} color="#fff" /> : 'Create Account'}
            </Button>
          </form>

          <div style={{
            marginTop: 24, paddingTop: 24,
            borderTop: '1px solid var(--border)',
            textAlign: 'center',
          }}>
            <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
              Already have an account?{' '}
              <Link
                to="/login"
                style={{
                  color: 'var(--accent-blue)',
                  fontWeight: 600,
                  textDecoration: 'none',
                }}
              >
                Sign in
              </Link>
            </p>
          </div>
        </Card>

        <p style={{
          textAlign: 'center', marginTop: 24,
          fontSize: 12, color: 'var(--text-faint)',
        }}>
          By creating an account, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
}
