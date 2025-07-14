'use client';

import { useEffect } from 'react';
import Image from 'next/image';
import { Menu, X } from 'lucide-react';
import { NavigationItem } from './NavigationItem';
import { ProfileSection } from './ProfileSection';
import { NavigationItem as NavigationItemType, User } from './types';

interface MobileNavigationProps {
  items: NavigationItemType[];
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
}

const mockUser: User = {
  name: 'Marc',
  avatar: '',
  id: '+49 800 00000321'
};

export function MobileNavigation({ items, isOpen, onToggle, onClose }: MobileNavigationProps) {
  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={onToggle}
        className="md:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-brand-navy-900 text-white hover:bg-brand-navy-700 transition-colors"
        aria-label="Toggle mobile menu"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onClose}
        />
      )}

      {/* Mobile Sidebar */}
      <div className={`
        md:hidden fixed left-0 top-0 h-full w-64 bg-brand-navy-900 text-white z-50
        transform transition-transform duration-medium ease-standard
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo Section */}
        <div className="flex items-center justify-between p-4 border-b border-white border-opacity-20">
          <div className="flex items-center">
            <Image
              src="/logos/Reddi_green_name.png"
              alt="Reddi"
              width={120}
              height={40}
              className="h-8 w-auto"
            />
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-white hover:bg-opacity-10 transition-colors"
            aria-label="Close mobile menu"
          >
            <X size={16} />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {items.map((item) => (
            <div key={item.id} onClick={onClose}>
              <NavigationItem
                item={item}
                isCollapsed={false}
                isMobile={true}
              />
            </div>
          ))}
        </nav>

        {/* Profile Section */}
        <ProfileSection user={mockUser} isCollapsed={false} />
      </div>
    </>
  );
}