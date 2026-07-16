import { Card } from './Card'
import { InboxIcon } from './icons'
import { Button } from './Button'

interface EmptyStateProps {
  title?: string
  message?: string
  actionLabel?: string
  onAction?: () => void
  'data-testid'?: string
}

export function EmptyState({
  title = 'No data available',
  message = 'There are no records to display at this time.',
  actionLabel,
  onAction,
  'data-testid': dataTestId,
}: EmptyStateProps) {
  return (
    <Card className="state state--empty" data-testid={dataTestId || 'empty-state'}>
      <div className="state__icon" aria-hidden="true">
        <InboxIcon className="icon--xl" />
      </div>
      <h3 className="state__title">{title}</h3>
      <p className="state__message">{message}</p>
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction} data-action="empty-action">
          {actionLabel}
        </Button>
      )}
    </Card>
  )
}
