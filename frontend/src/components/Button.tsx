import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from './icons'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  isLoading?: boolean
  fullWidth?: boolean
  'data-action'?: string
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  leftIcon,
  rightIcon,
  isLoading,
  fullWidth,
  className,
  disabled,
  'data-action': dataAction,
  ...rest
}: ButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        'btn',
        `btn--${variant}`,
        `btn--${size}`,
        fullWidth && 'btn--full-width',
        className,
      )}
      disabled={disabled || isLoading}
      data-action={dataAction || rest.onClick?.name || children?.toString()}
      data-loading={isLoading || undefined}
      {...rest}
    >
      {isLoading ? <span className="btn__spinner" aria-hidden="true" /> : leftIcon}
      <span className="btn__label">{children}</span>
      {rightIcon}
    </button>
  )
}
