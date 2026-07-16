import { Card } from './Card'
import { LoaderIcon } from './icons'

interface LoadingStateProps {
  title?: string
  message?: string
  'data-testid'?: string
}

export function LoadingState({
  title = 'Loading',
  message = 'Retrieving the latest data…',
  'data-testid': dataTestId,
}: LoadingStateProps) {
  return (
    <Card className="state state--loading" data-testid={dataTestId || 'loading-state'}>
      <div className="state__icon" aria-hidden="true">
        <LoaderIcon className="icon--xl" />
      </div>
      <h3 className="state__title">{title}</h3>
      <p className="state__message">{message}</p>
    </Card>
  )
}
