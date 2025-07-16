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
      hidden md:flex flex-col h-screen bg-brand-navy-900 text-white
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
              width={32}
              height={32}
              className="w-8 h-8"
            />
          </div>
        ) : (
          /* Expanded state - rocket + text logo */
          <div className="flex items-center">
            <Image
              src="/logos/yellow-cohete.png"
              alt="Rocket"
              width={28}
              height={28}
              className="w-7 h-7"
            />
            <Image
              src="/logos/Reddi_green_name.png"
              alt="Reddi"
              width={90}
              height={32}
              className="h-7 w-auto ml-2"
            />
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