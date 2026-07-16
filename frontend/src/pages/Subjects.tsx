import { Button } from '../components/Button'
import { StatusBadge } from '../components/Badge'
import { DataTable } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { PageHeader } from '../components/PageHeader'
import { ApprovalGate } from '../components/ApprovalGate'
import { ArrowRightIcon, UsersIcon } from '../components/icons'
import { useApi } from '../hooks/useApi'
import { useState } from 'react'

interface Subject {
  id: number
  subject_number: string
  screening_id: string
  enrolment_status: string
  randomisation_arm: string | null
}

export default function Subjects() {
  const { data: subjects, loading, error, refetch } = useApi<Subject>('/api/v1/subjects')
  const [approvalOpen, setApprovalOpen] = useState(false)

  return (
    <div>
      <PageHeader
        title="Subjects"
        subtitle="Enrolment, screening, and randomisation records"
        actions={
          <Button
            leftIcon={<UsersIcon />}
            rightIcon={<ArrowRightIcon />}
            onClick={() => setApprovalOpen(true)}
            data-action="enrol-subject"
          >
            Enrol subject
          </Button>
        }
      />

      {approvalOpen && (
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <ApprovalGate
            title="Enrol new subject"
            description="Subject enrolment must be performed under protocol and after informed consent has been documented. Confirm before proceeding."
            riskLevel="high"
            onApprove={() => setApprovalOpen(false)}
            onCancel={() => setApprovalOpen(false)}
          />
        </div>
      )}

      {loading && <LoadingState title="Loading subjects" />}
      {error && <ErrorState title="Failed to load subjects" message={error} onRetry={refetch} />}

      {!loading && !error && subjects && (
        <DataTable
          caption="Subjects"
          keyExtractor={(s) => s.id}
          rows={subjects}
          empty={
            <EmptyState
              title="No subjects found"
              message="There are no enrolled subjects in the system yet."
              actionLabel="Enrol subject"
              onAction={() => setApprovalOpen(true)}
            />
          }
          columns={[
            { key: 'subject_number', header: 'Subject Number', cell: (s) => <strong>{s.subject_number}</strong> },
            { key: 'screening_id', header: 'Screening ID', cell: (s) => s.screening_id },
            { key: 'status', header: 'Status', cell: (s) => <StatusBadge status={s.enrolment_status} /> },
            { key: 'arm', header: 'Arm', cell: (s) => s.randomisation_arm || <span className="badge badge--neutral">Not randomised</span> },
          ]}
        />
      )}
    </div>
  )
}
