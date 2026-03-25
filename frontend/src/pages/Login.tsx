import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../services/auth';
import toast from 'react-hot-toast';

export default function Login() {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await authService.login(formData);
      if (result.success) {
        toast.success(`Welcome back, ${result.username}`);
        navigate('/');
      }
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-white">
      {/* Left side: Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 lg:p-16">
        <div className="w-full max-w-sm space-y-8">
          <div className="flex items-center space-x-3 absolute top-8 left-8">
            <img src="/train_logo.jpg" alt="Logo" className="w-12 h-12 rounded-xl object-cover" />
            <span className="text-4xl font-bold tracking-tight text-gray-900 ml-1">RMS</span>
          </div>

          <div className="text-center">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">Login to your account</h1>
            <p className="mt-2 text-sm text-gray-500 font-medium">
              Enter your officer credentials below to access the system
            </p>
          </div>

          <form onSubmit={handleLogin} className="mt-10 space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700">Email</label>
              <input
                type="email"
                required
                className="mt-1.5 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all sm:text-sm"
                placeholder="m@example.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label className="block text-sm font-semibold text-gray-700">Password</label>
                <Link to="#" className="text-xs font-semibold text-gray-500 hover:text-black transition-colors">
                  Forgot your password?
                </Link>
              </div>
              <input
                type="password"
                required
                className="mt-1.5 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all sm:text-sm"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-bold text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black transition-all disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Login'}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-gray-500">
            Don't have an account?{' '}
            <Link to="/register" className="font-bold text-gray-950 hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>

      {/* Right side: Railway Image with Direct Content Overlay */}
      <div className="hidden lg:flex w-1/2 bg-gray-100 items-center justify-center relative overflow-hidden">
        <img 
          src="/railway_image.jpg" 
          alt="Railway System" 
          className="absolute inset-0 w-full h-full object-cover grayscale-[0.2]"
        />
        <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"></div>
        <div className="relative z-10 px-16 text-left w-full">
          <h2 className="text-white text-6xl font-black tracking-tighter leading-none mb-6 drop-shadow-2xl">
            Rescheduling <br/>Management <br/>System
          </h2>
          <div className="h-1.5 w-24 bg-white mb-8 rounded-full"></div>
          <p className="text-white/90 text-xl font-bold max-w-md leading-relaxed drop-shadow-lg">
            Multi-Agent Neural Network for Advanced Rail Infrastructure
          </p>
        </div>
      </div>
    </div>
  );
}
