import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface Props { children: React.ReactNode; fallback?: React.ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error.message, info.componentStack?.slice(0, 300))
    // Could send to telemetry here
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex items-center justify-center min-h-[400px] p-8">
          <Card className="p-6 max-w-md text-center space-y-4">
            <AlertTriangle className="w-12 h-12 mx-auto text-destructive" />
            <h2 className="text-lg font-semibold">Something went wrong</h2>
            <p className="text-sm text-muted-foreground break-all">
              {this.state.error.message}
            </p>
            <Button
              variant="outline"
              onClick={() => this.setState({ error: null })}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Try again
            </Button>
          </Card>
        </div>
      )
    }
    return this.props.children
  }
}
