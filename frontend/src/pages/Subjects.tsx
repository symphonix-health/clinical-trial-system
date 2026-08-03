import { Button } from '../components/Button'
import { StatusBadge } from '../components/Badge'
import { DataTable } from '../components/DataTable'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { PageHeader } from '../components/PageHeader'
import { ArrowRightIcon, UsersIcon } from '../components/icons'
import { useApi } from '../hooks/useApi'
import axios from 'axios'
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
  const [formOpen, setFormOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null)
  const [studyId, setStudyId] = useState('1')
  const [siteId, setSiteId] = useState('1')
  const [screeningId, setScreeningId] = useState('SCR-HEADED-001')

  const handleEnrol = async () => {
    setSubmitting(true)
    setResult(null)
    try {
      // Step 1: Create subject
      const subjRes = await axios.post('/api/v1/subjects', {
        study_id: Number(studyId),
        site_id: Number(siteId),
        screening_id: screeningId,
        demographics: { age: 50, sex: 'M' },
      })
      const subject = subjRes.data
      // Step 2: Record consent (this triggers the cascade via notify_subject_enrolled)
      await axios.post(`/api/v1/subjects/${subject.id}/consent`, {
        subject_id: subject.id,
        consent_version: 'v1.0',
        consent_date: new Date().toISOString(),
        document_reference: 'consent_headed_test.pdf',
      })
      setResult({ ok: true, msg: `Subject ${subject.subject_number} enrolled and consented. Cascade dispatched.` })
      setFormOpen(false)
      refetch()
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Enrolment failed'
      setResult({ ok: false, msg })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Subjects"
        subtitle="Enrolment, screening, and randomisation records"
        actions={
          <Button
            leftIcon={<UsersIcon />}
            rightIcon={<ArrowRightIcon />}
            onClick={() => { setFormOpen(true); setResult(null) }}
            data-action="enrol-subject"
          >
            Enrol subject
          </Button>
        }
      />

      {formOpen && (
        <div style={{
          background: 'var(--surface-card, #fff)',
          border: '1px solid var(--border, #e2e8f0)',
          borderRadius: 'var(--radius-lg, 12px)',
          padding: 'var(--space-6, 24px)',
          marginBottom: 'var(--space-6, 24px)',
          maxWidth: 480,
        }}>
          <h3 style={{ margin: '0 0 16px 0' }}>Enrol New Subject</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
              Study ID
              <input type="number" value={studyId} onChange={e => setStudyId(e.target.value)}
                style={{ padding: '8px 12px', border: '1px solid var(--border, #e2e8f0)', borderRadius: 6, fontSize: 14 }} />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
              Site ID
              <input type="number" value={siteId} onChange={e => setSiteId(e.target.value)}
                style={{ padding: '8px 12px', border: '1px solid var(--border, #e2e8f0)', borderRadius: 6, fontSize: 14 }} />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 14 }}>
              Screening ID
              <input type="text" value={screeningId} onChange={e => setScreeningId(e.target.value)}
                style={{ padding: '8px 12px', border: '1px solid var(--border, #e2e8f0)', borderRadius: 6, fontSize: 14 }} />
            </label>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <Button onClick={handleEnrol} disabled={submitting}
                data-action="confirm-enrol">
                {submitting ? 'Enrolling...' : 'Confirm Enrolment'}
              </Button>
              <Button onClick={() => setFormOpen(false)} disabled={submitting}
                style={{ background: 'var(--surface-muted, #f1f5f9)', color: 'var(--text, #334155)' }}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {result && (
        <div style={{
          padding: '12px 16px',
          borderRadius: 8,
          marginBottom: 16,
          background: result.ok ? '#ecfdf5' : '#fef2f2',
          color: result.ok ? '#065f46' : '#991b1b',
          border: `1px solid ${result.ok ? '#a7f3d0' : '#fecaca'}`,
        }}>
          {result.msg}
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
              onAction={() => setFormOpen(true)}
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
