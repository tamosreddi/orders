'use client';

import { usePathname } from 'next/navigation';
import { NavigationSidebar } from './NavigationSidebar';
import { MobileNavigation } from './MobileNavigation';
import { useNavigation } from './NavigationContext';
import { NavigationItem } from './types';

const baseNavigationItems: NavigationItem[] = [
  {
    id: 'messages',
    label: 'Messages',
    href: '/messages',
    icon: 'MessageCircle',
    isDisabled: false
  },
  {
    id: 'orders',
    label: 'Orders',
    href: '/orders',
    icon: 'ShoppingCart'
  },
  {
    id: 'customers',
    label: 'Customers',
    href: '/customers',
    icon: 'Users'
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
  const pathname = usePathname();

  // Create navigation items with dynamic active state based on current route
  const navigationItems = baseNavigationItems.map(item => ({
    ...item,
    isActive: pathname.startsWith(item.href) && item.href !== '/'
  }));

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