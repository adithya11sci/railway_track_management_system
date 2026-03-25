import { useState } from 'react'
import { ClockIcon } from '@heroicons/react/24/outline'
import apiService from '../services/api'
import toast from 'react-hot-toast'

export default function TrainDelay() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [formData, setFormData] = useState({
    train_number: '',
    delay_minutes: '',
    current_location: '',
    affected_passengers: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)

    try {
      const data = await apiService.handleTrainDelay({
        train_number: formData.train_number,
        delay_minutes: parseInt(formData.delay_minutes),
        current_location: formData.current_location,
        affected_passengers: formData.affected_passengers
          ? parseInt(formData.affected_passengers)
          : undefined,
      })

      if (data.success) {
        setResult(data.data)
        toast.success('Train delay processed successfully!')
      } else {
        toast.error(data.error || 'Failed to process delay')
      }
    } catch (error) {
      toast.error('Failed to process train delay')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const loadExample = () => {
    setFormData({
      train_number: '12627',
      delay_minutes: '45',
      current_location: 'Katpadi Junction',
      affected_passengers: '850',
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Train Delay Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Handle train delays with automated AI-powered responses
          </p>
        </div>
        <button
          onClick={loadExample}
          className="btn-secondary text-sm"
        >
          Load Example
        </button>
      </div>

      <div className="space-y-6">
        {/* Input Form */}
        <div className="card">
          <div className="flex items-center mb-4">
            <ClockIcon className="h-6 w-6 text-orange-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">Delay Information</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Train Number *
                </label>
                <input
                  type="text"
                  required
                  value={formData.train_number}
                  onChange={(e) => setFormData({ ...formData, train_number: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 12627"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Delay (minutes) *
                </label>
                <input
                  type="number"
                  required
                  value={formData.delay_minutes}
                  onChange={(e) => setFormData({ ...formData, delay_minutes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 45"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Current Location *
                </label>
                <input
                  type="text"
                  required
                  value={formData.current_location}
                  onChange={(e) => setFormData({ ...formData, current_location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., Katpadi Junction"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Affected Passengers (optional)
                </label>
                <input
                  type="number"
                  value={formData.affected_passengers}
                  onChange={(e) => setFormData({ ...formData, affected_passengers: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., 850"
                />
              </div>
            </div>

            <div className="flex justify-center pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full md:w-1/3 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing...
                  </span>
                ) : (
                  'Process Delay'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Response</h2>

          {!result && !loading && (
            <div className="text-center py-12 text-gray-400">
              <ClockIcon className="h-12 w-12 mx-auto mb-3" />
              <p>Submit delay information to see AI response</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">AI agents are processing...</p>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              
              {/* Intelligent Agent Execution Report */}
              <div className="bg-white border text-left border-gray-200 shadow-sm rounded-lg p-5 mt-4 text-gray-800">
                <div className="flex items-center space-x-2 mb-4 border-b pb-2">
                  <ClockIcon className="h-6 w-6 text-blue-600" />
                  <h3 className="text-xl font-semibold text-gray-800">AI Response & Orchestration</h3>
                </div>

                {/* General Info */}
                <div className="grid grid-cols-2 gap-4 mb-4 bg-gray-50 p-3 rounded-md">
                  <div>
                    <span className="text-xs font-semibold uppercase text-gray-500 block">Train Identifier</span>
                    <span className="text-sm font-medium">{result.train_number}</span>
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase text-gray-500 block">Agent Route Status</span>
                    <span className="text-sm px-2 py-1 bg-green-100 text-green-700 font-bold rounded">
                      {result?.plan?.route_status?.replace('_', ' ').toUpperCase() || 'PROCESSED'}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase text-gray-500 block">Disaster Triggered</span>
                    <span className="text-sm font-medium">{result?.plan?.disaster_triggered ? 'Yes 🚨' : 'No ✔️'}</span>
                  </div>
                  <div>
                    <span className="text-xs font-semibold uppercase text-gray-500 block">Orchestrator Loops</span>
                    <span className="text-sm font-medium">{result?.plan?.iteration || 1} Iteration(s)</span>
                  </div>
                </div>

                {/* AI Justification (New) */}
                {result?.multi_agent_pipeline?.ai_justification && (
                  <div className="mb-4 text-sm bg-blue-50 border border-blue-100 p-4 rounded-md shadow-inner">
                    <h4 className="font-bold text-blue-900 flex items-center mb-2">
                       <span className="mr-2">🤖</span> AI Agent Reasoning & Justification
                    </h4>
                    <p className="text-blue-800 leading-relaxed italic">
                      "{result.multi_agent_pipeline.ai_justification}"
                    </p>
                  </div>
                )}

                {/* Scheduling / Route Impact*/}
                {result?.plan?.results?.scheduling && (
                  <div className="mb-4 text-sm mt-4">
                     <h4 className="font-semibold text-blue-800 flex items-center mb-2">📋 Scheduling Insight</h4>
                     <ul className="list-disc list-inside ml-4 space-y-1 text-gray-600">
                       <li><span className="font-semibold text-gray-800">Route Assigned:</span> {result.plan.results.scheduling.assigned_route?.source} to {result.plan.results.scheduling.assigned_route?.destination}</li>
                       <li><span className="font-semibold text-gray-800">Departure:</span> {result.plan.results.scheduling.scheduled_departure} | <span className="font-semibold text-gray-800">Arrival:</span> {result.plan.results.scheduling.estimated_arrival}</li>
                     </ul>
                  </div>
                )}

                {/* Predication Output */}
                {result?.plan?.results?.prediction && (
                   <div className="mb-4 text-sm bg-indigo-50 border border-indigo-100 p-3 rounded-md">
                     <h4 className="font-semibold text-indigo-800 flex items-center mb-2">⏱️ Live AI Prediction</h4>
                     <p className="text-indigo-900 mb-1"><span className="font-semibold">Expected Platform Arrival:</span> {result.plan.results.prediction.predicted_arrival_time}</p>
                     <p className="text-indigo-900 mb-1"><span className="font-semibold">Analysis:</span> {result.plan.results.prediction.prediction_reasoning}</p>
                     <div className="mt-2 text-xs font-mono text-indigo-700">Calculated under {result.plan.results.prediction.weather_conditions} conditions, with {result.plan.results.prediction.congestion_level} congestion.</div>
                   </div>
                )}

                {/* Monitoring Report */}
                {result?.plan?.results?.monitoring && (
                   <div className="mb-4 text-sm bg-yellow-50 border border-yellow-100 p-3 rounded-md">
                      <h4 className="font-semibold text-yellow-800 flex items-center mb-2">📡 Arrival Monitoring Report</h4>
                      <p className="text-yellow-900 mb-1"><span className="font-semibold">Status:</span> {result.plan.results.monitoring.status}</p>
                      <p className="text-yellow-900 mb-1"><span className="font-semibold">Delay Detected:</span> {result.plan.results.monitoring.delay_minutes} minutes</p>
                      <p className="text-yellow-900"><span className="font-semibold">Risk Level Assessment:</span> {result.plan.results.monitoring.risk_level}</p>
                   </div>
                )}
                
                {/* Disaster Response (if applicable) */}
                {result?.plan?.results?.disaster && result.plan.results.disaster.length > 0 && (
                   <div className="mb-4 text-sm bg-red-50 border border-red-100 p-3 rounded-md">
                      <h4 className="font-semibold text-red-800 flex items-center mb-2">🚨 Disaster Recovery Plan Triggered</h4>
                      <p className="text-red-900">{typeof result.plan.results.disaster === 'string' ? result.plan.results.disaster : JSON.stringify(result.plan.results.disaster)}</p>
                   </div>
                )}

                {/* Dynamic Timetable Update UI */}
                {result?.timetable_updated && (
                   <div className={`mt-4 p-4 border rounded-md shadow-sm ${result.conflict_msg ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                      <h4 className={`font-bold text-lg mb-2 ${result.conflict_msg ? 'text-red-800' : 'text-green-800'}`}>
                        {result.conflict_msg ? '⚠️ Critical Collision Detected' : '✅ Timetable Successfully Rescheduled'}
                      </h4>
                      <div className="text-sm text-gray-700">
                         <p>The core Timetable Dataset was dynamically updated.</p>
                         <p className="mt-1">
                            <strong>Train {result.train_number}</strong> 
                            {result.original_arrival !== '--' ? ' arrival slot ' : ' departure slot '}
                            of <span className="line-through text-gray-500">
                              {result.original_arrival !== '--' ? result.original_arrival : result.original_departure}
                            </span> has been patched to <span className="font-bold text-black">
                              {result.new_arrival !== '--' ? result.new_arrival : result.new_departure}
                            </span>.
                          </p>
                         {result.conflict_msg && (
                           <div className="mt-2 p-2 bg-red-100 text-red-900 rounded border border-red-300">
                             <strong>URGENT AGENT ACTION:</strong> {result.conflict_msg}
                             <br/><span className="text-xs text-red-700 mt-1 block">Live tracking dashboard dataset updated to route conflict via alternate track.</span>
                           </div>
                         )}
                         <p className="mt-3 text-xs opacity-75">Check the <i>Timetable</i> view on the sidebar, where the modified time is actively synchronized!</p>
                      </div>
                   </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
