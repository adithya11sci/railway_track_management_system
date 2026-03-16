import React, { useState, useEffect } from 'react';

const Timetable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/timetable')
      .then((res) => res.json())
      .then((res) => {
        if (res.success) {
          setData(res.data);
        } else {
          setError(res.message);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4">Loading timetable...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Chennai Central Timetable</h1>
      <div className="overflow-x-auto bg-white shadow-md rounded-lg">
        <table className="min-w-full text-sm text-left text-gray-500">
          <thead className="text-xs text-gray-700 uppercase bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3">Train</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3">Source</th>
              <th className="px-6 py-3">Destination</th>
              <th className="px-6 py-3">Arrival</th>
              <th className="px-6 py-3">Departure</th>
              <th className="px-6 py-3">Platform</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 50).map((row, i) => (
              <tr key={i} className="bg-white border-b hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">
                  {row.train_id} - {row.train_name}
                </td>
                <td className="px-6 py-4">{row.train_type}</td>
                <td className="px-6 py-4">{row.source_station}</td>
                <td className="px-6 py-4">{row.destination_station}</td>
                <td className="px-6 py-4">{row.scheduled_arrival}</td>
                <td className="px-6 py-4">{row.scheduled_departure}</td>
                <td className="px-6 py-4 text-center">{row.platform}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 50 && (
          <div className="p-4 text-sm text-center text-gray-500 bg-gray-50">
            Showing first 50 of {data.length} records.
          </div>
        )}
      </div>
    </div>
  );
};

export default Timetable;