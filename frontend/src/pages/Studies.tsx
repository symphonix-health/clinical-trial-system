import { useState } from 'react'
import { Button } from '../components/Button'
import { StatusBadge } from '../components/Badge'
import { DataTable } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { PageHeader } from '../components/PageHeader'
import { ApprovalGate } from '../components/ApprovalGate'
import { ArrowRightIcon, FlaskConicalIcon } from '../components/icons'
import { useApi } from '../hooks/useApi'

interface Study {
  id: number
  protocol_number: string
  title: string
  phase: string
  status: string
  therapeutic_area: string
}

export default function Studies() {
  const { data: studies, loading, error, refetch } = useApi<Study>('/api/v1/studies')
  const [approvalOpen, setApprovalOpen] = useState(false)

  return (
    <div>
      <PageHeader
        title="Studies"
        subtitle="Manage protocols, amendments, and study lifecycle"
        actions={
          <Button
            leftIcon={<FlaskConicalIcon />}
            rightIcon={<ArrowRightIcon />}
            onClick={() => setApprovalOpen(true)}
            data-action="create-study"
          >
            Create study
          </Button>
        }
      />

      {approvalOpen && (
        <div className="page-header__actions" style={{ marginBottom: 'var(--space-6)' }}>
          <ApprovalGate
            title="Create new study"
            description="Creating a study is a regulated action. Confirm that the protocol has been reviewed and that the principal investigator has signed off."
            riskLevel="medium"
            onApprove={() => setApprovalOpen(false)}
            onCancel={() => setApprovalOpen(false)}
          />
        </div>
      )}

      {loading && <LoadingState title="Loading studies" />}
      {error && <ErrorState title="Failed to load studies" message={error} onRetry={refetch} />}

      {!loading && !error && studies && (
        <DataTable
          caption="Studies"
          keyExtractor={(s) => s.id}
          rows={studies}
          empty={
            <EmptyState
              title="No studies found"
              message="There are no studies in the system yet. Create a study to begin."
              actionLabel="Create study"
              onAction={() => setApprovalOpen(true)}
            />
          }
          columns={[
            { key: 'protocol', header: 'Protocol', cell: (s) => <strong>{s.protocol_number}</strong> },
            { key: 'title', header: 'Title', cell: (s) => s.title },
            { key: 'phase', header: 'Phase', cell: (s) => s.phase },
            { key: 'status', header: 'Status', cell: (s) => <StatusBadge status={s.status} /> },
            { key: 'area', header: 'Therapeutic Area', cell: (s) => s.therapeutic_area },
          ]}
        />
      )}
    </div>
  )
}
