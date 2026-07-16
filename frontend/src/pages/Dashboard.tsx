import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/Card'
import { Badge } from '../components/Badge'
import { LoadingState } from '../components/LoadingState'
import { ErrorState } from '../components/ErrorState'
import { PageHeader } from '../components/PageHeader'
import { BotIcon, FlaskConicalIcon, UsersIcon } from '../components/icons'
import { useApiObject } from '../hooks/useApi'

interface Health {
  status: string
  version: string
  timestamp: string
}

export default function Dashboard() {
  const { data: health, loading, error, refetch } = useApiObject<Health>('/api/v1/health')

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle="Clinical trial operations at a glance"
      />

      {loading && !health && <LoadingState title="Loading dashboard" />}
      {error && <ErrorState title="Health check failed" message={error} onRetry={refetch} />}

      {health && (
        <>
          <div className="stats-grid">
            <Card className="stat-card" data-testid="health-stat">
              <div className="stat-card__label">System status</div>
              <div className="stat-card__value">
                <Badge variant={health.status === 'ok' ? 'success' : 'warning'}>
                  {health.status}
                </Badge>
              </div>
              <div className="stat-card__meta">Version {health.version}</div>
            </Card>

            <Card className="stat-card">
              <div className="stat-card__label">Studies</div>
              <div className="stat-card__value">
                <FlaskConicalIcon className="icon" /> —
              </div>
              <div className="stat-card__meta">Navigate to Studies for details</div>
            </Card>

            <Card className="stat-card">
              <div className="stat-card__label">Subjects</div>
              <div className="stat-card__value">
                <UsersIcon className="icon" /> —
              </div>
              <div className="stat-card__meta">Navigate to Subjects for details</div>
            </Card>

            <Card className="stat-card">
              <div className="stat-card__label">Agent subjects</div>
              <div className="stat-card__value">
                <BotIcon className="icon" /> —
              </div>
              <div className="stat-card__meta">Navigate to Agent Subjects</div>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Platform health</CardTitle>
              <CardDescription>Last updated: {new Date(health.timestamp).toLocaleString()}</CardDescription>
            </CardHeader>
            <CardContent>
              <p data-testid="health-message">
                The CTMS backend is <Badge variant={health.status === 'ok' ? 'success' : 'warning'}>{health.status}</Badge> and running version{' '}
                <strong>{health.version}</strong>. Use the command palette (Ctrl+K) or sidebar to navigate between modules.
              </p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
