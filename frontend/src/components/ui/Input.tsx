import { forwardRef, InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  icon?: ReactNode;
  onIconClick?: () => void;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, id, icon, onIconClick, className = '', ...props }, ref) => {
    return (
      <div className={`relative space-y-2 ${className}`}>
        <label htmlFor={id} className="block text-[12px] font-medium tracking-wide text-gray-700">
          {label}
        </label>
        <div className="relative">
          <input
            id={id}
            ref={ref}
            className="border-surface-border bg-surface-muted focus:border-primary focus:ring-primary block w-full rounded-xl border px-4 py-3 text-sm text-gray-900 transition-all outline-none placeholder:text-gray-400 focus:ring-1"
            {...props}
          />
          {icon && (
            <button
              type="button"
              onClick={onIconClick}
              className="absolute top-1/2 right-4 -translate-y-1/2 text-gray-400 transition-colors hover:text-gray-600 focus:outline-none"
            >
              {icon}
            </button>
          )}
        </div>
      </div>
    );
  }
);
Input.displayName = 'Input';
