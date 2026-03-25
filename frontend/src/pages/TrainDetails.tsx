import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, ClockIcon, MapIcon } from '@heroicons/react/24/outline';

export default function TrainDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [trainData, setTrainData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/train/${id}`)
      .then((res) => res.json())
      .then((res) => {
        if (res.success) {
          setTrainData(res.data);
        } else {
          setError(res.message);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  if (loading) return <div className="p-8 text-center text-lg">Loading train details...</div>;
  if (error) return <div className="p-8 text-center text-red-500 text-lg">Error: {error}</div>;
  if (!trainData) return <div className="p-8 text-center text-gray-500">Train not found.</div>;

  const { info, simulation } = trainData;
  const stations = simulation.all_stations || [];

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <button 
          onClick={() => navigate('/timetable')}
          className="flex items-center text-indigo-600 hover:text-indigo-800 transition-colors bg-white px-4 py-2 rounded-md shadow-sm border border-gray-200 font-medium text-sm"
        >
          <ArrowLeftIcon className="w-5 h-5 mr-2" />
          Back to Timetable
        </button>
        <button 
          onClick={() => navigate('/train-delay')}
          className="bg-amber-100 hover:bg-amber-200 text-amber-800 px-4 py-2 rounded-md font-bold text-sm transition-colors border border-amber-300 shadow-sm"
        >
          Report Delay for {info.train_id}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-100">
        {/* Header Block */}
        <div className="bg-indigo-600 p-6 text-white flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{info.train_id} - {info.train_name}</h1>
            <p className="opacity-80 mt-1">{info.train_type} | {info.railway_zone}</p>
          </div>
          <div className="text-right flex flex-col items-end">
            <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold bg-white text-indigo-800 shadow-sm">
              Platform {info.platform}
            </span>
          </div>
        </div>

        {/* Schedule & Stats Top Block */}
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
            <ClockIcon className="w-6 h-6 mr-2 text-indigo-500" />
            Schedule & Route Details
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gray-50 rounded-lg p-5 border border-gray-200 hover:shadow-md transition-shadow">
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-3 font-bold border-b border-gray-200 pb-2">Terminals</p>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-gray-400 font-medium">Source</p>
                  <p className="font-bold text-gray-900 text-base">{info.source_station} <span className="text-sm font-normal text-gray-500">({info.source_code})</span></p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 font-medium">Destination</p>
                  <p className="font-bold text-gray-900 text-base">{info.destination_station} <span className="text-sm font-normal text-gray-500">({info.destination_code})</span></p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-5 border border-gray-200 hover:shadow-md transition-shadow">
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-3 font-bold border-b border-gray-200 pb-2">Timings</p>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-gray-400 font-medium">Scheduled Departure</p>
                  <p className="font-bold text-gray-900 text-base">{info.scheduled_departure}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 font-medium">Scheduled Arrival</p>
                  <p className="font-bold text-gray-900 text-base">{info.scheduled_arrival}</p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-50 to-white rounded-lg p-5 border border-indigo-100 hover:shadow-md transition-shadow">
               <p className="text-xs text-indigo-400 uppercase tracking-widest mb-3 font-bold border-b border-indigo-100 pb-2">Journey Stats</p>
               <div className="space-y-4">
                 <div>
                   <p className="text-xs text-indigo-400 font-medium">Total Distance / Duration</p>
                   <p className="font-bold text-indigo-900 text-base">{simulation.distance} km <span className="text-sm font-normal text-indigo-600">/ {simulation.duration} hrs</span></p>
                 </div>
                 <div>
                   <p className="text-xs text-indigo-400 font-medium">Average Speed</p>
                   <p className="font-bold text-indigo-900 text-base">{simulation.avg_speed} km/h</p>
                 </div>
               </div>
            </div>
          </div>
        </div>

        {/* Live Tracking Bottom Block */}
        <div className="p-8 bg-slate-50">
          <div className="flex justify-between items-end mb-14 border-b border-gray-200 pb-4">
            <h3 className="text-xl font-bold text-gray-800 flex items-center">
              <MapIcon className="w-6 h-6 mr-2 text-indigo-500" />
              Live Tracking Simulation
            </h3>
            <div className="text-right">
              <p className="text-xs text-gray-500 uppercase tracking-widest font-bold">Current Status</p>
              <div className="flex items-center mt-1">
                <div className={`w-3 h-3 rounded-full mr-2 ${simulation.status === 'On Time' ? 'bg-green-500 animate-pulse' : 'bg-amber-500'}`}></div>
                <p className={`font-bold text-lg ${simulation.status === 'On Time' ? 'text-green-700' : 'text-amber-700'}`}>
                  {simulation.status}
                </p>
              </div>
            </div>
          </div>
          
          <div className="relative pt-12 pb-16 px-4 max-w-5xl mx-auto overflow-x-hidden">
            {/* Background Track Line */}
            <div className="absolute top-10 left-0 w-full h-2.5 bg-gray-200 rounded-full shadow-inner"></div>
            
            {/* Active Progress Line */}
            <div 
              className="absolute top-10 left-0 h-2.5 bg-gradient-to-r from-indigo-400 to-indigo-600 rounded-full transition-all duration-1000 z-0 shadow-sm" 
              style={{ width: `${simulation.progress_percent}%` }}
            ></div>

            {/* Render all stations proportionally */}
            {stations.map((station: string, index: number) => {
              const positionPercent = stations.length > 1 ? (index / (stations.length - 1)) * 100 : 50;
              const isPassed = positionPercent <= (simulation.progress_percent || 0) + 1; // +1 to account for visual buffer

              return (
                <div 
                  key={index}
                  className="absolute top-7 flex flex-col items-center transform -translate-x-1/2 z-10"
                  style={{ left: `${positionPercent}%` }}
                  title={station}
                >
                  <div className={`w-7 h-7 rounded-full border-4 shadow-md transition-colors duration-500 ${
                    isPassed ? 'bg-indigo-600 border-indigo-100' : 'bg-white border-gray-300'
                  }`}></div>
                  <div className="mt-3 text-xs font-bold text-gray-600 text-center w-24 sm:w-32 drop-shadow-sm min-h-[40px]">
                    {station}
                  </div>
                </div>
              );
            })}
            
            {/* Train Icon positioned dynamically */}
            <div 
              className="absolute top-2 transform -translate-x-1/2 transition-all duration-1000 z-20" 
              style={{ left: `${simulation.progress_percent}%` }}
            >
              <div className="relative bg-indigo-700 text-white p-2 rounded-xl shadow-xl flex items-center justify-center border-2 border-indigo-300">
                <span className="text-2xl drop-shadow-md leading-none">🚆</span>
                {/* Pointer tip of tooltip */}
                <div className="absolute -bottom-2.5 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[8px] border-l-transparent border-t-[10px] border-t-indigo-700 border-r-[8px] border-r-transparent filter drop-shadow"></div>
              </div>
            </div>
          </div>
          
          {/* Tracking Text Summary */}
          <div className="mt-6 text-center max-w-2xl mx-auto">
            <div className="bg-indigo-50 py-4 px-6 rounded-xl border border-indigo-100 shadow-sm inline-block">
              <p className="text-[15px] text-indigo-900">
                Currently en route taking track <span className="font-bold bg-white px-2 py-0.5 rounded shadow-sm border border-indigo-50"># {info.track_number || 1}</span> between 
                <span className="font-bold ml-1">{simulation.current_station}</span> 
                <span className="px-2 text-indigo-400">→</span> 
                <span className="font-bold">{simulation.next_station}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}