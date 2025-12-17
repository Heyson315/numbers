import React from 'react';

interface Props { children: React.ReactNode }
interface State { hasError: boolean; error?: Error }

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // In real app: send to logging backend
    console.error('ErrorBoundary caught error', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '1rem', border: '1px solid #e57373', background: '#ffebee' }}>
          <h3 style={{ marginTop: 0 }}>Something went wrong.</h3>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.75rem' }}>{this.state.error?.message}</pre>
          <button onClick={() => this.setState({ hasError: false, error: undefined })}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}
