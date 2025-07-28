export interface NavigationItem {
  id: string;
  label: string;
  href: string;
  icon: string;
  isActive?: boolean;
  isDisabled?: boolean;
  hasNotification?: boolean;
}

export interface User {
  name: string;
  avatar: string;
  id: string;
}

export interface NavigationState {
  isCollapsed: boolean;
  isMobileMenuOpen: boolean;
}