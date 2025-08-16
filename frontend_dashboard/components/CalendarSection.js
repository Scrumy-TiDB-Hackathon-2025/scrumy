import { useState, useRef, useEffect } from 'react';
import { Calendar, Users } from 'lucide-react';

// Simple calendar popup for one month
function CalendarPopup({ selectedDate, onSelect, onClose }) {
  const popupRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (popupRef.current && !popupRef.current.contains(event.target)) {
        onClose();
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const year = selectedDate.getFullYear();
  const month = selectedDate.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const daysArray = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  return (
    <div
      ref={popupRef}
      className="absolute z-10 mt-2 left-0 bg-white border border-gray-200 rounded-xl shadow-lg p-5"
      style={{ minWidth: 240 }}
    >
      <div className="flex justify-between items-center mb-3">
        <span className="font-bold text-lg text-gray-800">
          {selectedDate.toLocaleString('default', { month: 'long' })} {year}
        </span>
        <button className="text-gray-400 hover:text-gray-700 text-xl" onClick={onClose}>✕</button>
      </div>
      <div className="grid grid-cols-7 gap-y-3 gap-x-2">
        {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map(d => (
          <div key={d} className="text-xs text-gray-400 text-center font-medium">{d}</div>
        ))}
        {Array(new Date(year, month, 1).getDay()).fill(null).map((_, i) => (
          <div key={`empty-${i}`} />
        ))}
        {daysArray.map(day => {
          const dateObj = new Date(year, month, day);
          const isSelected = dateObj.toDateString() === selectedDate.toDateString();
          return (
            <button
              key={day}
              className={`w-7 h-7 rounded-full text-xs text-center flex items-center justify-center transition
                ${isSelected ? 'bg-blue-600 text-white font-bold shadow' : 'hover:bg-blue-100 text-gray-700'}
              `}
              style={{ margin: '2px' }}
              onClick={() => { onSelect(dateObj); onClose(); }}
            >
              {day}
            </button>
          );
        })}
      </div>
    </div>
  );
}

const CalendarSection = ({ upcomingMeetings }) => {
  const today = new Date();
  const [selectedDate, setSelectedDate] = useState(today);
  const [showCalendar, setShowCalendar] = useState(false);
  const iconRef = useRef(null);

  // Generate a week range centered on today
  const generateWeekDays = () => {
    const days = [];
    for (let i = -3; i <= 3; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push({
        date: date.getDate(),
        isToday: i === 0,
        fullDate: date.toISOString().slice(0, 10),
        isSelected: date.toDateString() === selectedDate.toDateString(),
      });
    }
    return days;
  };

  const weekDays = generateWeekDays();

  const handleDayClick = (day) => {
    setSelectedDate(new Date(day.fullDate));
  };

  return (
    <div className="mb-8 relative">
      <h2 className="text-xl font-semibold mb-4 text-black">Calendar</h2>
      
      {/* Calendar Header with Date Selectors */}
      <div className="flex items-center justify-between mb-6">
        {/* Current Date Display */}
        <div className="flex items-center gap-2 relative">
          <Calendar size={20} className="text-blue-600" />
          <span className="font-medium text-black">
            {selectedDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
          </span>
          {/* Calendar icon triggers popup */}
          <button
            ref={iconRef}
            className="ml-2 p-2 rounded hover:bg-blue-100 relative"
            onClick={() => setShowCalendar(v => !v)}
            aria-label="Select date"
            type="button"
          >
            <Calendar size={20} className="text-black" />
            {showCalendar && (
              <div className="absolute left-0 top-full">
                <CalendarPopup
                  selectedDate={selectedDate}
                  onSelect={setSelectedDate}
                  onClose={() => setShowCalendar(false)}
                />
              </div>
            )}
          </button>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Date Selectors */}
          <div className="flex gap-2">
            {weekDays.map((day, index) => (
              <div
                key={index}
                className={`text-center p-2 rounded-full min-w-[36px] h-[36px] flex items-center justify-center cursor-pointer text-sm transition
                  ${day.isSelected ? 'bg-blue-500 text-white font-medium' : 'text-black'}
                  ${!day.isSelected ? 'hover:bg-blue-100' : ''}
                `}
                onClick={() => handleDayClick(day)}
                title={day.fullDate}
              >
                <span>{day.date}</span>
              </div>
            ))}
          </div>
          
          {/* Navigation arrows */}
          <div className="flex gap-1">
            <button className="p-1 hover:bg-gray-100 rounded text-black" disabled>‹</button>
            <button className="p-1 hover:bg-gray-100 rounded text-black" disabled>›</button>
          </div>
        </div>
      </div>

      {/* Today's Meetings - 4 card spaces in one line */}
      <div className="grid grid-cols-4 gap-4">
        {/* Meeting Card 1 */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
          <h3 className="font-medium text-gray-900 mb-1 text-sm">Hackathon Alignme...</h3>
          <p className="text-xs text-gray-500 mb-2">6 - 7pm</p>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Users size={12} />
            4 guests
          </div>
        </div>
        
        {/* Meeting Card 2 */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
          <h3 className="font-medium text-gray-900 mb-1 text-sm">Hackathon Alignme...</h3>
          <p className="text-xs text-gray-500 mb-2">6 - 7pm</p>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Users size={12} />
            4 guests
          </div>
        </div>
        
        {/* Empty Card 3 */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 min-h-[80px]">
          {/* Empty card space */}
        </div>
        
        {/* Empty Card 4 */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-100 min-h-[80px]">
          {/* Empty card space */}
        </div>
      </div>
    </div>
  );
};

export default CalendarSection;
// ...existing code...