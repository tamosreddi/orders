'use client';

import { usePathname } from 'next/navigation';
import { NavigationSidebar } from './NavigationSidebar';
import { MobileNavigation } from './MobileNavigation';
import { useNavigation } from './NavigationContext';
import { NavigationItem } from './types';
import { useHasUnreadMessages } from '@/lib/hooks/useHasUnreadMessages';

const baseNavigationItems: NavigationItem[] = [
  {
    id: 'messages',
    label: 'Mensajes',
    href: '/messages',
    icon: 'MessageCircle',
    isDisabled: false
  },
  {
    id: 'orders',
    label: 'Órdenes',
    href: '/orders',
    icon: 'ShoppingCart'
  },
  {
    id: 'customers',
    label: 'Clientes',
    href: '/customers',
    icon: 'Users'
  },
  {
    id: 'catalog',
    label: 'Catálogo',
    href: '/catalog',
    icon: 'Tag',
    isDisabled: true
  },
  {
    id: 'settings',
    label: 'Configuración',
    href: '/settings',
    icon: 'Settings',
    isDisabled: true
  },
  {
    id: 'help',
    label: 'Ayuda',
    href: '/help',
    icon: 'HelpCircle',
    isDisabled: true
  }
];

export function NavigationMenu() {
  const { navigationState, toggleCollapsed, toggleMobileMenu, closeMobileMenu } = useNavigation();
  const pathname = usePathname();
  const { hasUnreadMessages } = useHasUnreadMessages();

  // Create navigation items with dynamic active state and notification state
  const navigationItems = baseNavigationItems.map(item => ({
    ...item,
    isActive: pathname.startsWith(item.href) && item.href !== '/',
    hasNotification: item.id === 'messages' ? hasUnreadMessages : false
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