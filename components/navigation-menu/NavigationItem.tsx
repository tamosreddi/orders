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
    ? 'bg-white bg-opacity-10 text-white' 
    : 'text-white text-opacity-85 hover:text-white hover:bg-white hover:bg-opacity-5';
    
  const disabledClasses = item.isDisabled 
    ? 'opacity-50 cursor-not-allowed' 
    : 'cursor-pointer';

  const content = (
    <>
      <IconComponent size={24} className="flex-shrink-0" />
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