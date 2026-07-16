import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from './icons'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  variant?: 'default' | 'interactive' | 'elevated'
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function Card({
  children,
  variant = 'default',
  padding = 'md',
  className,
  ...rest
}: CardProps) {
  return (
    <div
      className={cn('card', `card--${variant}`, `card--pad-${padding}`, className)}
      {...rest}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('card__header', className)} {...rest}>
      {children}
    </div>
  )
}

export function CardTitle({
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn('card__title', className)} {...rest}>
      {children}
    </h3>
  )
}

export function CardDescription({
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn('card__description', className)} {...rest}>
      {children}
    </p>
  )
}

export function CardContent({
  children,
  className,
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('card__content', className)} {...rest}>
      {children}
    </div>
  )
}
