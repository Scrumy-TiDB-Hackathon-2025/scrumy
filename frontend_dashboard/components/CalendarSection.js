import { useState, useRef } from 'react';
import { Calendar, Users } from 'lucide-react';
import { DatePicker } from 'antd';
import dayjs from "dayjs";
import 'antd/dist/reset.css'; // Ensure Ant Design styles are loaded

const CalendarSection = ({ upcomingMeetings }) => {
  const today = new Date();
  const [selectedDate, setSelectedDate] = useState(today);
  const [showCalendar, setShowCalendar] = useState(false);
  const iconRef = useRef(null);

  // Generate a week range centered on selectedDate
  const generateWeekDays = () => {
    const days = [];
    for (let i = -3; i <= 3; i++) {
      const date = new Date(selectedDate);
      date.setDate(selectedDate.getDate() + i);
      days.push({
        date: date.getDate(),
        isToday: date.toDateString() === today.toDateString(),
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

  // Handler for Ant Design DatePicker
  const handleDateChange = (date) => {
    if (date) {
      setSelectedDate(date.toDate());
    }
    setShowCalendar(false);
  };

  return (
    <div className="bg-white rounded-xl shadow border border-gray-100 px-6 py-4">
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
          {/* Calendar icon triggers Ant Design DatePicker */}
          <div className="ml-2 relative">
            <button
              ref={iconRef}
              className="p-2 rounded hover:bg-blue-100"
              onClick={() => setShowCalendar(v => !v)}
              aria-label="Select date"
              type="button"
            >
              <Calendar size={20} className="text-black" />
            </button>
            {showCalendar && (
              <div className="absolute left-0 top-full z-10 mt-2">
                <DatePicker
                  open={true}
                  onChange={handleDateChange}
                  onOpenChange={setShowCalendar}
                  value={dayjs(selectedDate)}
                  style={{ minWidth: 220 }}
                  getPopupContainer={node => node.parentNode}
                  autoFocus
                />
              </div>
            )}
          </div>
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
    </div>
  );
};

export default CalendarSection;
// ...existing code...