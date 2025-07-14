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
        {!isCollapsed && (
          <div className="flex items-center">
            <Image
              src="/logos/Reddi_green_name.png"
              alt="Reddi"
              width={120}
              height={40}
              className="h-8 w-auto"
            />
          </div>
        )}
        <button
          onClick={onToggleCollapsed}
          className="p-1 rounded-md hover:bg-white hover:bg-opacity-10 transition-colors"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <ChevronRight size={16} />
          ) : (
            <ChevronLeft size={16} />
          )}
        </button>
      </div>

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