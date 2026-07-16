import { useState } from 'react'
import { Button } from '../components/Button'
import { StatusBadge } from '../components/Badge'
import { DataTable } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { PageHeader } from '../components/PageHeader'
import { ApprovalGate } from '../components/ApprovalGate'
import { ArrowRightIcon, BotIcon } from '../components/icons'
import { useApi } from '../hooks/useApi'

interface AgentSubject {
  id: number
  principal_id: string
  persona_key: string
  autonomy_level: string
  safety_class: string
  attestation_status: string
}

export default function AgentSubjects() {
  const { data: agents, loading, error, refetch } = useApi<AgentSubject>('/api/v1/agents/subjects')
  const [approvalOpen, setApprovalOpen] = useState(false)

  return (
    <div>
      <PageHeader
        title="Agent Subjects"
        subtitle="Autonomous persona subjects under protocol supervision"
        actions={
          <Button
            leftIcon={<BotIcon />}
            rightIcon={<ArrowRightIcon />}
            onClick={() => setApprovalOpen(true)}
            data-action="register-agent-subject"
          >
            Register agent subject
          </Button>
        }
      />

      {approvalOpen && (
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <ApprovalGate
            title="Register agent subject"
            description="Registering an autonomous agent subject requires safety attestation and PI approval. Confirm that the agent's autonomy level and safety class have been reviewed."
            riskLevel="high"
            confirmationText="I confirm this agent subject has been safety-attested"
            onApprove={() => setApprovalOpen(false)}
            onCancel={() => setApprovalOpen(false)}
          />
        </div>
      )}

      {loading && <LoadingState title="Loading agent subjects" />}
      {error && <ErrorState title="Failed to load agent subjects" message={error} onRetry={refetch} />}

      {!loading && !error && agents && (
        <DataTable
          caption="Agent subjects"
          keyExtractor={(a) => a.id}
          rows={agents}
          empty={
            <EmptyState
              title="No agent subjects found"
              message="There are no agent subjects registered in the system yet."
              actionLabel="Register agent subject"
              onAction={() => setApprovalOpen(true)}
            />
          }
          columns={[
            { key: 'principal', header: 'Principal', cell: (a) => <code>{a.principal_id}</code> },
            { key: 'persona', header: 'Persona', cell: (a) => a.persona_key },
            { key: 'autonomy', header: 'Autonomy', cell: (a) => <StatusBadge status={a.autonomy_level} /> },
            { key: 'safety', header: 'Safety Class', cell: (a) => a.safety_class },
            { key: 'attestation', header: 'Attestation', cell: (a) => <StatusBadge status={a.attestation_status} /> },
          ]}
        />
      )}
    </div>
  )
}
