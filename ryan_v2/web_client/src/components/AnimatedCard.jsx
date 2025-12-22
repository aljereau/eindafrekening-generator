import React from 'react';
import clsx from 'clsx';

/**
 * AnimatedCard
 * 
 * A reusable component that implements the "Ryan V2" Sidebar animation style.
 * 
 * Key Features:
 * 1. slide-right on active (`translate-x-1`)
 * 2. icon scale-up on hover (`group-hover:scale-110`)
 * 3. smooth transitions (`transition-all duration-300`)
 */
export default function AnimatedCard({
    active = false,
    icon,
    title,
    subtitle,
    onClick,
    colorClass = "bg-blue-600" // Pass Tailwind color classes here
}) {
    return (
        <div
            onClick={onClick}
            className={clsx(
                // --- Base Layout ---
                "group flex items-center gap-4 p-4 rounded-lg cursor-pointer border",

                // --- ANIMATION ENGINE ---
                // This makes the movement and color changes smooth
                "transition-all duration-300",

                // --- ACTIVE VS INACTIVE STATE ---
                active
                    ? "bg-white border-gray-200 shadow-md translate-x-1" // Active: White bg, shadow, slight move right
                    : "border-transparent hover:bg-white/50 hover:border-white/50" // Inactive: Transparent, subtle hover bg
            )}
        >
            {/* --- ICON CONTAINER --- */}
            <div className={clsx(
                "w-12 h-12 rounded-md flex items-center justify-center text-white shadow-lg",

                // --- ICON ANIMATION ---
                // Scales up the icon when the *parent card* (group) is hovered
                "transition-transform group-hover:scale-110 duration-300",

                // Color & Focus Ring
                colorClass,
                active ? "ring-4 ring-black/5" : ""
            )}>
                {icon}
            </div>

            {/* --- TEXT CONTENT --- */}
            <div className="flex-1 min-w-0">
                <h4 className={clsx(
                    "text-base font-bold truncate transition-colors",
                    // Darken text on active or hover
                    active ? "text-gray-900" : "text-gray-500 group-hover:text-gray-900"
                )}>
                    {title}
                </h4>

                {subtitle && (
                    <p className="text-xs text-gray-400 truncate font-medium mt-0.5">
                        {subtitle}
                    </p>
                )}
            </div>
        </div>
    );
}
