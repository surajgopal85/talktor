// src/components/layout/Navbar.tsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Stethoscope, Mic, BarChart3, Settings, Users } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;
  
  const navItems = [
    { path: '/', label: 'Translator', icon: Mic },
    { path: '/dashboard', label: 'Dashboard', icon: BarChart3 },
    { path: '/sessions', label: 'Sessions', icon: Users },
    { path: '/settings', label: 'Settings', icon: Settings }
  ];

  return (
    <nav className="bg-white shadow-lg border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3">
            <Stethoscope className="text-blue-600" size={32} />
            <span className="text-2xl font-bold text-gray-800">talktor</span>
          </Link>

          {/* Navigation */}
          <div className="flex space-x-8">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive(path)
                    ? 'text-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon size={18} />
                <span>{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};
