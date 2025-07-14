'use client';

import { NavigationSidebar } from './NavigationSidebar';
import { MobileNavigation } from './MobileNavigation';
import { useNavigation } from './NavigationContext';
import { NavigationItem } from './types';

const navigationItems: NavigationItem[] = [
  {
    id: 'messages',
    label: 'Messages',
    href: '/messages',
    icon: 'MessageCircle',
    isDisabled: true
  },
  {
    id: 'marketing',
    label: 'Marketing',
    href: '/marketing',
    icon: 'Megaphone',
    isDisabled: true
  },
  {
    id: 'orders',
    label: 'Orders',
    href: '/orders',
    icon: 'ShoppingCart',
    isActive: true
  },
  {
    id: 'customers',
    label: 'Customers',
    href: '/customers',
    icon: 'Users',
    isDisabled: true
  },
  {
    id: 'catalog',
    label: 'Catalog',
    href: '/catalog',
    icon: 'Tag',
    isDisabled: true
  },
  {
    id: 'settings',
    label: 'Settings',
    href: '/settings',
    icon: 'Settings',
    isDisabled: true
  },
  {
    id: 'help',
    label: 'Get help',
    href: '/help',
    icon: 'HelpCircle',
    isDisabled: true
  }
];

export function NavigationMenu() {
  const { navigationState, toggleCollapsed, toggleMobileMenu, closeMobileMenu } = useNavigation();

  return (
    <>
      {/* Desktop Sidebar */}
      <NavigationSidebar
        items={navigationItems}
        isCollapsed={navigationState.isCollapsed}
        onToggleCollapsed={toggleCollapsed}
      />

      {/* Mobile Navigation */}
      <MobileNavigation
        items={navigationItems}
        isOpen={navigationState.isMobileMenuOpen}
        onToggle={toggleMobileMenu}
        onClose={closeMobileMenu}
      />
    </>
  );
}