import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from './icons'

export type BadgeVariant =
  | 'default'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'pending'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode
  variant?: BadgeVariant
  dot?: boolean
}

const statusToVariant: Record<string, BadgeVariant> = {
  approved: 'success',
  active: 'success',
  enrolled: 'success',
  attested: 'success',
  attested_active: 'success',
  draft: 'neutral',
  pending: 'pending',
  screening: 'info',
  rejected: 'danger',
  failed: 'danger',
  withdrawn: 'danger',
  completed: 'success',
  suspended: 'warning',
  amended: 'warning',
  monitoring: 'info',
  closed: 'neutral',
}

export function Badge({ children, variant, dot, className, ...rest }: BadgeProps) {
  const resolved = variant || statusToVariant[String(children).toLowerCase()] || 'default'
  return (
    <span
      className={cn('badge', `badge--${resolved}`, dot && 'badge--dot', className)}
      data-status={String(children)}
      {...rest}
    >
      {dot && <span className="badge__dot" aria-hidden="true" />}
      {children}
    </span>
  )
}

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <Badge variant={statusToVariant[status.toLowerCase()]} className={className}>
      {status}
    </Badge>
  )
}
