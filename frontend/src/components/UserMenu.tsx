'use client';

import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';
import { LogOut } from 'lucide-react';

type UserMenuProps = {
  collapsed?: boolean;
};

export default function UserMenu({ collapsed = false }: UserMenuProps) {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) return <div className="h-10 w-20 animate-pulse rounded bg-slate-200"></div>;

  if (collapsed) {
    return (
      <div
        className="flex cursor-pointer justify-center rounded-xl p-2 hover:bg-slate-200"
        title={user?.full_name}
      >
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-[11px] font-bold uppercase text-white shadow-sm">
          {user?.full_name?.[0] || 'U'}
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <Link
        href="/login"
        className="flex w-full justify-center rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-primary-hover"
      >
        Đăng nhập
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-[12px] font-bold uppercase text-white shadow-sm">
        {user.full_name ? user.full_name[0] : 'U'}
      </div>
      <div className="flex-1 overflow-hidden">
        <p className="truncate text-[13px] font-semibold text-slate-800">{user.full_name || 'Người dùng'}</p>
        <p className="truncate text-[11px] text-slate-500">{user.email}</p>
      </div>
      <button
        onClick={logout}
        title="Đăng xuất"
        className="
          flex items-center gap-1.5
          rounded-xl
          border border-slate-200
          bg-white/70
          px-3 py-2
          text-[12px] font-semibold text-slate-600
          shadow-sm
          backdrop-blur
          transition-all
          hover:border-brand-pink/30
          hover:bg-brand-pink/10
          hover:text-brand-pink
          active:scale-95
        "
      >
        <LogOut size={14} />
        <span>Log out</span>
      </button>
    </div>
  );
}