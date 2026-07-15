/** Shared components barrel export
 *  统一导出所有共享组件，简化导入路径
 *
 *  使用示例:
 *    import { StatCard, AgentCard, StatusBadge } from '@/components/shared'
 */
export { StatCard } from './StatCard'
export { AgentCard } from './AgentCard'
export type { Agent } from './AgentCard'
export { StatusBadge } from './StatusBadge'
export { PageHeader } from './PageHeader'
export { EmptyState } from './EmptyState'
export { LoadingState } from './LoadingState'
export { ErrorState } from './ErrorState'
