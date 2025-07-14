'use client';

import Image from 'next/image';
import { User } from './types';

interface ProfileSectionProps {
  user: User;
  isCollapsed: boolean;
}

export function ProfileSection({ user, isCollapsed }: ProfileSectionProps) {
  return (
    <div className="border-t border-white border-opacity-20 pt-4">
      <div className="flex items-center gap-3 px-4 py-3">
        <div className="w-8 h-8 rounded-full bg-white bg-opacity-20 flex items-center justify-center flex-shrink-0">
          <span className="text-white text-sm font-medium">
            {user.name.charAt(0).toUpperCase()}
          </span>
        </div>
        {!isCollapsed && (
          <div className="flex-1 min-w-0">
            <p className="text-white text-sm font-medium truncate">
              {user.name}
            </p>
            <p className="text-white text-opacity-60 text-xs truncate">
              {user.id}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}