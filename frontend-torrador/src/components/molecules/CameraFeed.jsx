import React from 'react';

export const CameraFeed = () => {
  return (
    <div className="flex flex-col bg-[#292524] rounded-3xl shadow-xl border border-stone-800 overflow-hidden w-full relative group">
      
      <div className="absolute top-4 left-4 right-4 flex justify-between items-center z-10">
        <div className="bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
          <span className="text-stone-200 font-medium text-xs tracking-wide">REC • Sensor Visual</span>
        </div>
        <span className="bg-black/40 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 text-stone-300 text-xs font-mono">
          YOLOv8 + CLIP
        </span>
      </div>

      <div className="aspect-video bg-[#151312] relative overflow-hidden">
        
        <img 
  src="http://localhost:8000/video_feed" 
  alt="Feed do Torrador" 
  className="w-full h-full object-cover"
/>
        
        <div className="absolute top-10 left-10 w-8 h-8 border-t-2 border-l-2 border-amber-500/50"></div>
        <div className="absolute top-10 right-10 w-8 h-8 border-t-2 border-r-2 border-amber-500/50"></div>
        <div className="absolute bottom-10 left-10 w-8 h-8 border-b-2 border-l-2 border-amber-500/50"></div>
        <div className="absolute bottom-10 right-10 w-8 h-8 border-b-2 border-r-2 border-amber-500/50"></div>
      </div>
    </div>
  );
};