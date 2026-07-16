import type { ReactNode } from 'react'
import { cn } from './icons'

export interface Column<T> {
  key: string
  header: ReactNode
  width?: string
  align?: 'left' | 'center' | 'right'
  cell: (row: T) => ReactNode
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  keyExtractor: (row: T) => string | number
  caption?: string
  empty?: ReactNode
  className?: string
}

export function DataTable<T>({
  columns,
  rows,
  keyExtractor,
  caption,
  empty,
  className,
}: DataTableProps<T>) {
  if (rows.length === 0 && empty) {
    return <div className="data-table__empty">{empty}</div>
  }

  return (
    <div className={cn('data-table__scroll', className)}>
      <table className="data-table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                style={{ width: c.width }}
                className={c.align ? `data-table__cell--${c.align}` : undefined}
                scope="col"
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={keyExtractor(row)}>
              {columns.map((c) => (
                <td
                  key={c.key}
                  className={cn(
                    'data-table__cell',
                    c.align && `data-table__cell--${c.align}`,
                  )}
                >
                  {c.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
