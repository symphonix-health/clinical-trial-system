import { Card } from './Card'
import { AlertTriangleIcon } from './icons'
import { Button } from './Button'

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
  'data-testid'?: string
}

export function ErrorState({
  title = 'Unable to load data',
  message = 'Something went wrong while retrieving the requested information.',
  onRetry,
  'data-testid': dataTestId,
}: ErrorStateProps) {
  return (
    <Card
      className="state state--error"
      role="alert"
      aria-live="assertive"
      data-testid={dataTestId || 'error-state'}
    >
      <div className="state__icon" aria-hidden="true">
        <AlertTriangleIcon className="icon--xl" />
      </div>
      <h3 className="state__title">{title}</h3>
      <p className="state__message">{message}</p>
      {onRetry && (
        <Button variant="primary" size="sm" onClick={onRetry} data-action="retry-load">
          Retry
        </Button>
      )}
    </Card>
  )
}
