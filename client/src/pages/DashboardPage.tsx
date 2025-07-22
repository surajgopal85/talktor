// src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import { BarChart3, Users, Clock, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';

interface DashboardStats {
  totalSessions: number;
  activeSpecialties: string[];
  averageAccuracy: number;
  safetyAlertsTriggered: number;
  mostCommonLanguagePair: string;
  recentActivity: Array<{
    sessionId: string;
    specialty: string;
    timestamp: string;
    accuracy: number;
  }>;
}

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // This would call your analytics endpoint
        const response = await fetch('http://127.0.0.1:8000/analytics/dashboard');
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Mock data for now
        setStats({
          totalSessions: 247,
          activeSpecialties: ['OBGYN', 'General', 'Cardiology'],
          averageAccuracy: 94.2,
          safetyAlertsTriggered: 12,
          mostCommonLanguagePair: 'English → Spanish',
          recentActivity: [
            { sessionId: 'sess_123', specialty: 'OBGYN', timestamp: '2 hours ago', accuracy: 96.1 },
            { sessionId: 'sess_124', specialty: 'General', timestamp: '3 hours ago', accuracy: 92.8 },
            { sessionId: 'sess_125', specialty: 'OBGYN', timestamp: '5 hours ago', accuracy: 97.2 },
          ]
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Medical Translation Dashboard</h1>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <Users className="text-blue-600" size={24} />
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-800">{stats?.totalSessions}</h3>
                <p className="text-gray-600">Total Sessions</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <TrendingUp className="text-green-600" size={24} />
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-800">{stats?.averageAccuracy}%</h3>
                <p className="text-gray-600">Avg Accuracy</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <AlertTriangle className="text-orange-600" size={24} />
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-800">{stats?.safetyAlertsTriggered}</h3>
                <p className="text-gray-600">Safety Alerts</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <BarChart3 className="text-purple-600" size={24} />
              <div className="ml-4">
                <h3 className="text-lg font-semibold text-gray-800">{stats?.activeSpecialties.length}</h3>
                <p className="text-gray-600">Active Specialties</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Recent Translation Activity</h2>
          <div className="space-y-4">
            {stats?.recentActivity.map((activity) => (
              <div key={activity.sessionId} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <CheckCircle className="text-green-600" size={20} />
                  <div>
                    <p className="font-medium text-gray-800">{activity.specialty} Session</p>
                    <p className="text-sm text-gray-600">{activity.sessionId} • {activity.timestamp}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-green-600">{activity.accuracy}%</p>
                  <p className="text-xs text-gray-500">Accuracy</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};