/** Project selector — shadcn/ui edition. Popover + Command. */
import { useState } from 'react'
import { useProjectStore, type ProjectInfo } from '../stores/project'
import { ChevronDown, Plus, FolderOpen, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from '@/components/ui/command'
import { cn } from '@/lib/utils'

interface ProjectSelectorProps {
  onCreateProject?: () => void
}

export default function ProjectSelector({ onCreateProject }: ProjectSelectorProps) {
  const { t } = useTranslation()
  const projects = useProjectStore(s => s.projects)
  const activeId = useProjectStore(s => s.activeId)
  const activeProject = useProjectStore(s => s.activeProject())
  const setActive = useProjectStore(s => s.setActive)
  const loading = useProjectStore(s => s.loading)
  const error = useProjectStore(s => s.error)

  const [open, setOpen] = useState(false)

  const select = (p: ProjectInfo) => {
    setActive(p.id)
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px]',
            'bg-secondary border border-border cursor-pointer',
            'hover:bg-accent transition-colors'
          )}
        >
          <FolderOpen size={16} />
          <span className="max-w-[140px] truncate">
            {activeProject?.name || activeProject?.id || t('projectSelector.choose')}
          </span>
          <ChevronDown size={14} className={cn('transition-transform', open && 'rotate-180')} />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-[280px] p-0" align="start">
        <Command>
          <CommandInput placeholder={t('projectSelector.search')} />
          <CommandList>
            <CommandEmpty>{loading ? t('studio.common.loading') : t('projectSelector.empty')}</CommandEmpty>
            <CommandGroup>
              {projects.map(p => (
                <CommandItem
                  key={p.id}
                  value={p.name || p.id}
                  onSelect={() => select(p)}
                  className="flex items-center justify-between"
                >
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium">{p.name || p.id}</span>
                    <span className="text-[11px] text-muted-foreground">
                      {p.modules?.length || 0} {t('projectSelector.modules')}
                    </span>
                  </div>
                  {p.id === activeId && <Check size={14} className="text-primary" />}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
        <div className="border-t border-border p-1.5">
          {error && <div className="px-2 py-1 text-[11px] text-destructive truncate" title={error}>{error}</div>}
          <button
            type="button"
            onClick={() => { setOpen(false); onCreateProject?.() }}
            className="flex items-center justify-center gap-1 w-full px-2 py-2 rounded-md text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground border border-dashed border-border no-underline transition-colors"
          >
            <Plus size={14} /> {t('projectSelector.new')}
          </button>
        </div>
      </PopoverContent>
    </Popover>
  )
}
