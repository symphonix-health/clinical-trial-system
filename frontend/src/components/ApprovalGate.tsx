import { useState } from 'react'
import { Card } from './Card'
import { CheckCircleIcon, ShieldCheckIcon } from './icons'
import { Button } from './Button'

interface ApprovalGateProps {
  title: string
  description: string
  riskLevel?: 'low' | 'medium' | 'high'
  confirmationText?: string
  onApprove: () => void
  onCancel: () => void
  'data-testid'?: string
}

export function ApprovalGate({
  title,
  description,
  riskLevel = 'medium',
  confirmationText = 'I confirm this action',
  onApprove,
  onCancel,
  'data-testid': dataTestId,
}: ApprovalGateProps) {
  const [confirmed, setConfirmed] = useState(false)
  const [attempted, setAttempted] = useState(false)

  const handleApprove = () => {
    if (!confirmed) {
      setAttempted(true)
      return
    }
    onApprove()
  }

  return (
    <Card
      className={`gate gate--${riskLevel}`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="gate-title"
      data-testid={dataTestId || 'approval-gate'}
    >
      <div className="gate__header">
        <ShieldCheckIcon className="gate__icon" aria-hidden="true" />
        <div>
          <h3 id="gate-title" className="gate__title">
            {title}
          </h3>
          <p className="gate__description">{description}</p>
        </div>
      </div>

      <label
        className={cn('gate__checkbox', attempted && !confirmed && 'gate__checkbox--error')}
      >
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => {
            setConfirmed(e.target.checked)
            setAttempted(false)
          }}
          data-action="approval-confirm"
        />
        <span>{confirmationText}</span>
      </label>

      <div className="gate__actions">
        <Button variant="secondary" onClick={onCancel} data-action="approval-cancel">
          Cancel
        </Button>
        <Button
          variant={riskLevel === 'high' ? 'danger' : 'primary'}
          leftIcon={<CheckCircleIcon />}
          onClick={handleApprove}
          data-action="approval-confirm-action"
        >
          Confirm
        </Button>
      </div>
    </Card>
  )
}

function cn(...classes: Array<string | false | undefined>) {
  return classes.filter(Boolean).join(' ')
}
