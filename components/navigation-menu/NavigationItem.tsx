'use client';

import Link from 'next/link';
import { NavigationItem as NavigationItemType } from './types';
import { 
  MessageCircle, 
  Megaphone, 
  ShoppingCart, 
  Users, 
  Tag, 
  Settings, 
  HelpCircle 
} from 'lucide-react';

const iconMap = {
  MessageCircle,
  Megaphone,
  ShoppingCart,
  Users,
  Tag,
  Settings,
  HelpCircle
};

interface NavigationItemProps {
  item: NavigationItemType;
  isCollapsed: boolean;
  isMobile?: boolean;
}

export function NavigationItem({ item, isCollapsed, isMobile = false }: NavigationItemProps) {
  const IconComponent = iconMap[item.icon as keyof typeof iconMap];
  
  const baseClasses = `
    flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-150
    ${isMobile ? 'w-full' : ''}
  `;
  
  const activeClasses = item.isActive 
    ? 'bg-white bg-opacity-15 text-white shadow-sm' 
    : 'text-white text-opacity-70 hover:text-white hover:bg-white hover:bg-opacity-10';
    
  const disabledClasses = item.isDisabled 
    ? 'opacity-50 cursor-not-allowed' 
    : 'cursor-pointer';

  const content = (
    <>
      <div className="relative flex-shrink-0">
        <IconComponent size={24} />
        {item.hasNotification && (
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
        )}
      </div>
      {(!isCollapsed || isMobile) && (
        <span className="font-light text-base">{item.label}</span>
      )}
    </>
  );

  if (item.isDisabled) {
    return (
      <div className={`${baseClasses} ${activeClasses} ${disabledClasses}`}>
        {content}
      </div>
    );
  }

  return (
    <Link 
      href={item.href}
      className={`${baseClasses} ${activeClasses} ${disabledClasses}`}
    >
      {content}
    </Link>
  );
}