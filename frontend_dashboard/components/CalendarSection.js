export default function CalendarSection({ date, title, time, guests }) {
  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm w-52">
      <div className="flex items-center justify-between mb-2">
        <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded text-sm">
          {date}
        </span>
      </div>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-gray-500 text-sm">{time}</p>
      <p className="text-gray-400 text-xs">{guests}</p>
    </div>
  );
}
