import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../services/auth';
import toast from 'react-hot-toast';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      return toast.error('Passwords do not match');
    }
    setLoading(true);
    try {
      const result = await authService.register({
        username: formData.username,
        email: formData.email,
        password: formData.password
      });
      if (result.success) {
        toast.success('Registration successful! Please login.');
        navigate('/login');
      }
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      {/* Left side: Register Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 lg:p-24 relative">
        <div className="w-full max-w-sm space-y-8 py-12">
          <div className="flex items-center space-x-3 absolute top-8 left-8">
            <img src="/train_logo.jpg" alt="Logo" className="w-12 h-12 rounded-xl object-cover" />
            <span className="text-4xl font-bold tracking-tight text-gray-900 ml-1">RMS</span>
          </div>

          <div className="text-center">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">Create an account</h1>
            <p className="mt-2 text-sm text-gray-500 font-medium">
              Enter your details below to create your officer account
            </p>
          </div>

          <form onSubmit={handleRegister} className="mt-10 space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700">Username</label>
              <input
                type="text"
                required
                className="mt-1.5 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all sm:text-sm"
                placeholder="jdoe"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
              />
            </div>

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
              <label className="block text-sm font-semibold text-gray-700">Password</label>
              <input
                type="password"
                required
                className="mt-1.5 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all sm:text-sm"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700">Confirm Password</label>
              <input
                type="password"
                required
                className="mt-1.5 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-black focus:border-black transition-all sm:text-sm"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-bold text-white bg-black hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-black transition-all disabled:opacity-50"
            >
              {loading ? 'Initializing...' : 'Create Account'}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="font-bold text-gray-950 hover:underline">
              Login
            </Link>
          </p>
        </div>
      </div>

      {/* Right side: Railway Image with Direct Content Overlay */}
      <div className="hidden lg:flex w-1/2 bg-gray-100 items-center justify-center sticky top-0 h-screen overflow-hidden">
        <img 
          src="/railway_image.jpg" 
          alt="Railway System" 
          className="absolute inset-0 w-full h-full object-cover grayscale-[0.2]"
        />
        <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"></div>
        <div className="relative z-10 px-16 text-left w-full">
          <h2 className="text-white text-7xl font-black tracking-tighter leading-[0.9] mb-8 drop-shadow-2xl">
            OFFICER<br/>ACCESS
          </h2>
          <div className="h-2 w-32 bg-white mb-10 rounded-full"></div>
          <p className="text-white/95 text-2xl font-bold max-w-lg leading-snug drop-shadow-xl">
            Join the RMS Neural Network for Advanced Rail Rescheduling
          </p>
        </div>
      </div>
    </div>
  );
}
