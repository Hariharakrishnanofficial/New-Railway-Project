import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser, signin, saveTokens } from '../services/authApi';
import '../styles/AuthPage.css';

export default function AuthPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('signin');
  
  // Signin state
  const [signinData, setSigninData] = useState({ email: '', password: '' });
  const [signinError, setSigninError] = useState('');
  const [signinLoading, setSigninLoading] = useState(false);
  
  // Register state
  const [registerData, setRegisterData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phoneNumber: '',
    address: '',
  });
  const [registerError, setRegisterError] = useState('');
  const [registerLoading, setRegisterLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  // ══════════════════════════════════════════════════════════════════════════
  //  SIGNIN HANDLER
  // ══════════════════════════════════════════════════════════════════════════

  const handleSignin = async (e) => {
    e.preventDefault();
    setSigninError('');
    
    if (!signinData.email || !signinData.password) {
      setSigninError('Email and password are required');
      return;
    }

    setSigninLoading(true);
    try {
      const response = await signin(signinData.email, signinData.password);
      
      if (response.success) {
        const { access_token, refresh_token, user } = response.data;
        saveTokens(access_token, refresh_token);
        localStorage.setItem('user', JSON.stringify(user));
        
        navigate(user.role === 'Admin' ? '/admin/dashboard' : '/dashboard');
      } else {
        setSigninError(response.error || 'SignIn failed');
      }
    } catch (error) {
      setSigninError(error.response?.data?.error || 'SignIn failed. Please try again.');
    } finally {
      setSigninLoading(false);
    }
  };

  // ══════════════════════════════════════════════════════════════════════════
  //  REGISTER HANDLER
  // ══════════════════════════════════════════════════════════════════════════

  const validatePassword = (pwd) => {
    let strength = 0;
    if (pwd.length >= 8) strength += 25;
    if (pwd.length >= 12) strength += 25;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength += 25;
    if (/[0-9]/.test(pwd)) strength += 12;
    if (/[!@#$%^&*]/.test(pwd)) strength += 13;
    return Math.min(strength, 100);
  };

  const handleRegisterInputChange = (e) => {
    const { name, value } = e.target;
    setRegisterData(prev => ({ ...prev, [name]: value }));
    
    if (name === 'password') {
      setPasswordStrength(validatePassword(value));
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegisterError('');
    
    const { fullName, email, password, confirmPassword, phoneNumber, address } = registerData;
    
    if (!fullName || !email || !password || !confirmPassword) {
      setRegisterError('All required fields must be filled');
      return;
    }

    if (password !== confirmPassword) {
      setRegisterError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setRegisterError('Password must be at least 6 characters');
      return;
    }

    if (passwordStrength < 50) {
      setRegisterError('Password is too weak. Include uppercase, lowercase, and numbers');
      return;
    }

    setRegisterLoading(true);
    try {
      const response = await registerUser({
        fullName,
        email,
        password,
        phoneNumber,
        address,
      });
      
      if (response.success) {
        alert('Registration successful! Please signin with your credentials.');
        setActiveTab('signin');
        setRegisterData({
          fullName: '',
          email: '',
          password: '',
          confirmPassword: '',
          phoneNumber: '',
          address: '',
        });
        setSigninData({ email, password: '' });
      } else {
        setRegisterError(response.error || 'Registration failed');
      }
    } catch (error) {
      setRegisterError(error.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setRegisterLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        {/* Tab Navigation */}
        <div className="auth-tabs">
          <button
            className={`tab-btn ${activeTab === 'signin' ? 'active' : ''}`}
            onClick={() => setActiveTab('signin')}
          >
            Sign In
          </button>
          <button
            className={`tab-btn ${activeTab === 'register' ? 'active' : ''}`}
            onClick={() => setActiveTab('register')}
          >
            Register
          </button>
        </div>

        {/* SIGNIN FORM */}
        {activeTab === 'signin' && (
          <form onSubmit={handleSignin} className="auth-form">
            <h2>Sign In to Your Account</h2>
            
            {signinError && <div className="error-message">{signinError}</div>}
            
            <div className="form-group">
              <label htmlFor="signin-email">Email</label>
              <input
                id="signin-email"
                type="email"
                name="email"
                value={signinData.email}
                onChange={(e) => setSigninData({...signinData, email: e.target.value})}
                placeholder="your@email.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="signin-password">Password</label>
              <input
                id="signin-password"
                type="password"
                name="password"
                value={signinData.password}
                onChange={(e) => setSigninData({...signinData, password: e.target.value})}
                placeholder="••••••••"
                required
              />
            </div>

            <button type="submit" disabled={signinLoading} className="submit-btn">
              {signinLoading ? 'Signing in...' : 'Sign In'}
            </button>

            <p className="auth-link">Don't have an account? <a onClick={() => setActiveTab('register')}>Register here</a></p>
          </form>
        )}

        {/* REGISTER FORM */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegister} className="auth-form">
            <h2>Create New Account</h2>
            
            {registerError && <div className="error-message">{registerError}</div>}
            
            <div className="form-group">
              <label htmlFor="fullName">Full Name *</label>
              <input
                id="fullName"
                type="text"
                name="fullName"
                value={registerData.fullName}
                onChange={handleRegisterInputChange}
                placeholder="John Doe"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email *</label>
              <input
                id="email"
                type="email"
                name="email"
                value={registerData.email}
                onChange={handleRegisterInputChange}
                placeholder="your@email.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                id="password"
                type="password"
                name="password"
                value={registerData.password}
                onChange={handleRegisterInputChange}
                placeholder="••••••••"
                required
              />
              <div className="password-strength">
                <div className="strength-bar">
                  <div 
                    className={`strength-fill ${
                      passwordStrength < 33 ? 'weak' : 
                      passwordStrength < 66 ? 'medium' : 
                      'strong'
                    }`}
                    style={{ width: `${passwordStrength}%` }}
                  ></div>
                </div>
                <span className="strength-text">
                  {passwordStrength < 33 ? 'Weak' : 
                   passwordStrength < 66 ? 'Medium' : 
                   'Strong'}
                </span>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password *</label>
              <input
                id="confirmPassword"
                type="password"
                name="confirmPassword"
                value={registerData.confirmPassword}
                onChange={handleRegisterInputChange}
                placeholder="••••••••"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="phoneNumber">Phone Number</label>
              <input
                id="phoneNumber"
                type="tel"
                name="phoneNumber"
                value={registerData.phoneNumber}
                onChange={handleRegisterInputChange}
                placeholder="+1 (555) 123-4567"
              />
            </div>

            <div className="form-group">
              <label htmlFor="address">Address</label>
              <textarea
                id="address"
                name="address"
                value={registerData.address}
                onChange={handleRegisterInputChange}
                placeholder="Your address"
                rows="3"
              ></textarea>
            </div>

            <button type="submit" disabled={registerLoading} className="submit-btn">
              {registerLoading ? 'Creating Account...' : 'Create Account'}
            </button>

            <p className="auth-link">Already have an account? <a onClick={() => setActiveTab('signin')}>Sign in here</a></p>
          </form>
        )}
      </div>
    </div>
  );
}
