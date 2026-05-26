import { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'icon' | 'ghost';
  children: ReactNode;
}

export const Button = ({
  variant = 'primary',
  className = '',
  children,
  disabled,
  ...props
}: ButtonProps) => {
  const baseStyle = 'transition-all focus:outline-none flex items-center justify-center';

  const variants = {
    primary:
      'w-full rounded-3xl bg-primary px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-primary-hover focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-70 disabled:cursor-not-allowed',
    outline:
      'w-full gap-3 rounded-3xl border border-gray-300 bg-gray-50 px-4 py-3 text-sm font-semibold text-gray-900 shadow-sm hover:bg-gray-100',
    icon: 'p-1 text-white/50 hover:text-white',
    ghost: 'text-white/50 hover:text-white',
  };

  return (
    <button
      className={`${baseStyle} ${variants[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};
