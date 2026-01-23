'use client';

import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

type UserMenuProps = {
  collapsed?: boolean;
};

export default function UserMenu({ collapsed = false }: UserMenuProps) {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) return <div className="h-10 w-20 animate-pulse rounded bg-gray-200"></div>;

  if (collapsed) {
    return (
      <div
        className="flex cursor-pointer justify-center rounded-lg p-2 hover:bg-gray-200"
        title={user?.full_name}
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-600">
          {user?.full_name?.[0] || 'U'}
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
      >
        Đăng nhập
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-4 border-t border-gray-200 py-4">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 font-bold text-blue-600">
        {user.full_name ? user.full_name[0].toUpperCase() : 'U'}
      </div>
      <div className="flex-1 overflow-hidden">
        <p className="truncate text-sm font-medium text-white">{user.full_name || 'Người dùng'}</p>
        <p className="truncate text-xs text-gray-500">{user.email}</p>
      </div>
      <button
        onClick={logout}
        className="text-sm font-medium text-red-600 hover:text-red-800"
        title="Đăng xuất"
      >
        Thoát
      </button>
    </div>
  );
}
