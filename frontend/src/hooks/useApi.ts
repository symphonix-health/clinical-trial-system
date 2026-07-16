import { useCallback, useEffect, useState } from 'react'
import axios, { type AxiosError } from 'axios'

export interface ApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useApi<T>(url: string): ApiState<T[]> {
  const [data, setData] = useState<T[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get<T[]>(url)
      setData(res.data)
    } catch (err) {
      const message = axios.isAxiosError?.(err)
        ? err.response?.data?.detail || err.message
        : 'Unexpected error'
      setError(message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data: data as T[] | null, loading, error, refetch: fetch }
}

export function useApiObject<T>(url: string): ApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get<T>(url)
      setData(res.data)
    } catch (err) {
      const message = axios.isAxiosError?.(err)
        ? (err as AxiosError<{ detail?: string }>).response?.data?.detail || (err as Error).message
        : 'Unexpected error'
      setError(message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [url])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}
