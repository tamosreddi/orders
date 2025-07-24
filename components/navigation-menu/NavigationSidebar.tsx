'use client';

import Image from 'next/image';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { NavigationItem } from './NavigationItem';
import { ProfileSection } from './ProfileSection';
import { NavigationItem as NavigationItemType, User } from './types';

interface NavigationSidebarProps {
  items: NavigationItemType[];
  isCollapsed: boolean;
  onToggleCollapsed: () => void;
}

const mockUser: User = {
  name: 'Marc',
  avatar: '',
  id: '+49 800 00000321'
};

export function NavigationSidebar({ items, isCollapsed, onToggleCollapsed }: NavigationSidebarProps) {
  return (
    <div className={`
      hidden md:flex flex-col h-screen bg-reddi-green text-white
      transition-all duration-medium ease-standard fixed left-0 top-0 z-50
      ${isCollapsed ? 'w-16' : 'w-64'}
    `}>
      {/* Logo Section */}
      <div className="flex items-center justify-between p-4 border-b border-white border-opacity-20">
        {isCollapsed ? (
          /* Collapsed state - center the rocket */
          <div className="flex justify-center w-full">
            <Image
              src="/logos/yellow-cohete.png"
              alt="Rocket"
              width={40}
              height={48}
              className="w-10 h-auto object-contain"
            />
          </div>
        ) : (
          /* Expanded state - rocket + text logo */
          <div className="flex items-center">
            <Image
              src="/logos/yellow-cohete.png"
              alt="Rocket"
              width={36}
              height={44}
              className="w-9 h-auto object-contain"
            />
            <div className="ml-3 h-7 w-24 overflow-hidden flex items-center">
              <Image
                src="/logos/reddi_white.png"
                alt="Reddi"
                width={120}
                height={120}
                className="w-full h-auto object-cover scale-110"
              />
            </div>
          </div>
        )}
        
        {!isCollapsed && (
          <button
            onClick={onToggleCollapsed}
            className="p-1 rounded-md hover:bg-white hover:bg-opacity-10 transition-colors"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft size={16} />
          </button>
        )}
      </div>
      
      {/* Expand button for collapsed state */}
      {isCollapsed && (
        <div className="flex justify-center p-2">
          <button
            onClick={onToggleCollapsed}
            className="p-1 rounded-md hover:bg-white hover:bg-opacity-10 transition-colors"
            aria-label="Expand sidebar"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map((item) => (
          <NavigationItem
            key={item.id}
            item={item}
            isCollapsed={isCollapsed}
          />
        ))}
      </nav>

      {/* Profile Section */}
      <ProfileSection user={mockUser} isCollapsed={isCollapsed} />
    </div>
  );
}