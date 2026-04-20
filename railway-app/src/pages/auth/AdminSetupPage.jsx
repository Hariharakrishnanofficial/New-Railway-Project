/**
 * AdminSetupPage - First-time admin account setup.
 * Only works when no admin exists or with valid setup key.
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/SessionAuthContext';
import { useToast } from '../../context/ToastContext';
import { Button, Input, Card, Spinner, Icon } from '../../components/UI';
import api from '../../services/api';

export default function AdminSetupPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const toast = useToast();

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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!form.setupKey.trim()) {
      newErrors.setupKey = 'Setup key is required';
    }

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
    try {
      const res = await api.post('/auth/setup-admin', {
        setupKey: form.setupKey.trim(),
        fullName: form.fullName.trim(),
        email: form.email.trim().toLowerCase(),
        password: form.password,
        phoneNumber: form.phoneNumber.trim(),
      });

      const data = res.data?.data || res.data;

      if (data.status === 'success' || data.accessToken) {
        // Store tokens and user data
        if (data.accessToken) {
          localStorage.setItem('accessToken', data.accessToken);
        }
        if (data.refreshToken) {
          localStorage.setItem('refreshToken', data.refreshToken);
        }
        if (data.user) {
          localStorage.setItem('user', JSON.stringify(data.user));
        }

        toast.success('Admin account created successfully!');
        // Use HashRouter navigation instead of direct window.location
        window.location.hash = '#/admin';
      } else {
        toast.error(data.message || 'Setup failed');
      }
    } catch (err) {
      const message = err.response?.data?.message || err.message || 'Setup failed';
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

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="max-w-md w-full space-y-8 p-8">
        <div className="text-center">
          <Icon name="shield" className="mx-auto h-12 w-12 text-indigo-600" />
          <h2 className="mt-4 text-3xl font-extrabold text-gray-900">
            Admin Setup
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Create the first administrator account
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <Input
              label="Setup Key"
              name="setupKey"
              type="password"
              value={form.setupKey}
              onChange={handleChange}
              error={errors.setupKey}
              placeholder="Enter the setup key"
              required
            />

            <Input
              label="Full Name"
              name="fullName"
              type="text"
              value={form.fullName}
              onChange={handleChange}
              error={errors.fullName}
              placeholder="Enter your full name"
              required
            />

            <Input
              label="Email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              error={errors.email}
              placeholder="admin@example.com"
              required
            />

            <div className="relative">
              <Input
                label="Password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={handleChange}
                error={errors.password}
                placeholder="Minimum 8 characters"
                required
              />
              <button
                type="button"
                className="absolute right-3 top-8 text-gray-400 hover:text-gray-600"
                onClick={() => setShowPassword(!showPassword)}
              >
                <Icon name={showPassword ? 'eye-off' : 'eye'} size={20} />
              </button>
            </div>

            <Input
              label="Confirm Password"
              name="confirmPassword"
              type={showPassword ? 'text' : 'password'}
              value={form.confirmPassword}
              onChange={handleChange}
              error={errors.confirmPassword}
              placeholder="Confirm your password"
              required
            />

            <Input
              label="Phone Number (Optional)"
              name="phoneNumber"
              type="tel"
              value={form.phoneNumber}
              onChange={handleChange}
              error={errors.phoneNumber}
              placeholder="+1234567890"
            />
          </div>

          <Button
            type="submit"
            className="w-full"
            disabled={loading}
          >
            {loading ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Creating Admin...
              </>
            ) : (
              'Create Admin Account'
            )}
          </Button>

          <div className="text-center text-sm">
            <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
              Back to Login
            </Link>
          </div>

          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> The default setup key is{' '}
              <code className="bg-yellow-100 px-1 rounded">railway-admin-setup-2024</code>
              <br />
              This should be changed in production via the <code>ADMIN_SETUP_KEY</code> environment variable.
            </p>
          </div>
        </form>
      </Card>
    </div>
  );
}
