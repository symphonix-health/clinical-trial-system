import type { ReactNode } from 'react'
import { cn } from './icons'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  className?: string
}

export function PageHeader({ title, subtitle, actions, className }: PageHeaderProps) {
  return (
    <header className={cn('page-header', className)} data-testid="page-header">
      <div className="page-header__text">
        <h2 className="page-header__title">{title}</h2>
        {subtitle && <p className="page-header__subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header__actions">{actions}</div>}
    </header>
  )
}
