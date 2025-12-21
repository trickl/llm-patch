import { useCallback, useMemo, useState } from 'react'
import clsx from 'clsx'
import {
  Autocomplete,
  Badge,
  Box,
  Button,
  Chip,
  Collapse,
  Divider,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import FilterListIcon from '@mui/icons-material/FilterList'
import type { AnnotationState, CaseSummary } from '../types'
import { defaultAnnotation } from '../types'
import type { FiltersState, FilterKey } from '../store/useReviewStore'
import { CASE_STATUS_OPTIONS, deriveCaseStatus, type CaseStatusFilter } from '../utils/caseFilters'

const FIRST_ERROR_CATEGORY_LABELS: Record<string, string> = {
  '1': 'Syntactic / Local Structural',
  '2': 'Name Resolution / Imports / Scope',
  '3': 'Type / Signature / API Compatibility',
  '4': 'Control Flow / Contract Enforcement',
  '5': 'Build System / Dependency / Config',
  '6': 'Cross-Module Semantic / Architectural',
  '7': 'Linting / Style / Policy',
  unlabeled: 'Unlabeled',
}

function formatFirstErrorCategoryLabel(key: string): string {
  return FIRST_ERROR_CATEGORY_LABELS[key] ?? `Category ${key}`
}

interface CaseSidebarProps {
  cases: CaseSummary[]
  allCases: CaseSummary[]
  annotations: Record<string, AnnotationState>
  selectedId: string | null
  loading: boolean
  error: string | null
  onSelect: (caseId: string) => void
  filters: FiltersState
  onSetFilterValues: (key: FilterKey, values: string[]) => void
  onSetFingerprintQuery: (query: string) => void
  onClearFilters: () => void
  datasetRefreshing: boolean
  datasetRefreshError: string | null
  onRefreshDataset: () => Promise<void>
}

interface LanguageGroup {
  key: string
  label: string
  count: number
  categories: ErrorCategoryGroup[]
}

interface ErrorCategoryGroup {
  key: string
  label: string
  count: number
  algorithms: AlgorithmGroup[]
}

interface AlgorithmGroup {
  key: string
  label: string
  count: number
  statuses: StatusGroup[]
}

interface StatusGroup {
  key: CaseStatusFilter
  label: string
  count: number
  models: ModelGroup[]
}

interface ModelGroup {
  key: string
  label: string
  count: number
  cases: CaseSummary[]
}

export function CaseSidebar({
  cases,
  allCases,
  annotations,
  selectedId,
  loading,
  error,
  onSelect,
  filters,
  onSetFilterValues,
  onSetFingerprintQuery,
  onClearFilters,
  datasetRefreshing,
  datasetRefreshError,
  onRefreshDataset,
}: CaseSidebarProps) {
  const suiteLabel = allCases[0]?.problemId ?? 'Test Cases'
  const quickSearchActive = filters.fingerprintQuery.trim().length > 0
  const advancedFiltersActive =
    filters.languages.length +
    filters.errorCategories.length +
    filters.models.length +
    filters.algorithms.length +
    filters.statuses.length > 0
  const filterActive = quickSearchActive || advancedFiltersActive
  const filteredCount = cases.length
  const totalCount = allCases.length

  const languageOptions = useMemo(
    () => buildFilterOptions(allCases, (testCase) => testCase.language),
    [allCases],
  )
  const modelOptions = useMemo(
    () => buildFilterOptions(allCases, (testCase) => testCase.modelSlug),
    [allCases],
  )
  const algorithmOptions = useMemo(
    () => buildFilterOptions(allCases, (testCase) => testCase.algorithm),
    [allCases],
  )
  const errorCategoryOptions = useMemo(() => buildErrorCategoryOptions(allCases), [allCases])
  const statusOptions = useMemo(() => buildStatusOptions(allCases), [allCases])
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({})
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const caseTree = useMemo(() => buildCaseTree(cases), [cases])
  const isNodeExpanded = useCallback((nodeId: string) => expandedNodes[nodeId] ?? true, [expandedNodes])
  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => ({
      ...prev,
      [nodeId]: !(prev[nodeId] ?? true),
    }))
  }, [])

  const toggleAdvanced = useCallback(() => {
    setAdvancedOpen((prev) => !prev)
  }, [])

  const renderCaseEntry = useCallback((testCase: CaseSummary) => {
    const active = testCase.id === selectedId
    const annotation = annotations[testCase.id] ?? defaultAnnotation
    return (
      <li key={testCase.id}>
        <button
          type="button"
          className={clsx('sidebar__item', 'sidebar__item--compact', active && 'sidebar__item--active')}
          onClick={() => onSelect(testCase.id)}
        >
          <div className="sidebar__item-main">
            <div>
              <span className="sidebar__item-title">{testCase.filePath}</span>
              <span className="sidebar__item-subtitle">{testCase.modelSlug}</span>
              <span className="sidebar__item-subtitle">ID {testCase.fingerprint}</span>
            </div>
            <span className="sidebar__item-subtitle">{testCase.diffName}</span>
          </div>
          <div className="sidebar__chips">
            <StatusChip label="Src" value={annotation.sourceQuality} />
            <StatusChip label="Diff" value={annotation.diffQuality} />
            <OutcomeChip value={annotation.finalOutcome} />
            <PatchChip applied={testCase.patchApplied} success={testCase.success} />
          </div>
        </button>
      </li>
    )
  }, [annotations, onSelect, selectedId])

  const renderModelBranch = useCallback((model: ModelGroup, prefix: string) => {
    const nodeId = `${prefix}|model:${model.key}`
    const expanded = isNodeExpanded(nodeId)
    const containsSelection = model.cases.some((entry) => entry.id === selectedId)
    return (
      <div
        key={nodeId}
        className={clsx(
          'case-tree__node',
          'case-tree__node--level-4',
          containsSelection && 'is-highlighted',
          expanded && 'is-expanded',
        )}
      >
        <button type="button" className="case-tree__toggle" onClick={() => toggleNode(nodeId)} aria-expanded={expanded}>
          <span>{model.label}</span>
          <span className="case-tree__count">{model.count}</span>
        </button>
        {expanded && <ul className="case-tree__cases">{model.cases.map(renderCaseEntry)}</ul>}
      </div>
    )
  }, [isNodeExpanded, renderCaseEntry, selectedId, toggleNode])

  const renderStatusBranch = useCallback((status: StatusGroup, prefix: string) => {
    const nodeId = `${prefix}|status:${status.key}`
    const expanded = isNodeExpanded(nodeId)
    const containsSelection = status.models.some((model) => model.cases.some((entry) => entry.id === selectedId))
    return (
      <div
        key={nodeId}
        className={clsx(
          'case-tree__node',
          'case-tree__node--level-3',
          containsSelection && 'is-highlighted',
          expanded && 'is-expanded',
        )}
      >
        <button type="button" className="case-tree__toggle" onClick={() => toggleNode(nodeId)} aria-expanded={expanded}>
          <span>{status.label}</span>
          <span className="case-tree__count">{status.count}</span>
        </button>
        {expanded && (
          <div className="case-tree__children">
            {status.models.map((model) => renderModelBranch(model, nodeId))}
          </div>
        )}
      </div>
    )
  }, [isNodeExpanded, renderModelBranch, selectedId, toggleNode])

  const renderAlgorithmBranch = useCallback((algorithm: AlgorithmGroup, prefix: string) => {
    const nodeId = `${prefix}|algorithm:${algorithm.key}`
    const expanded = isNodeExpanded(nodeId)
    const containsSelection = algorithm.statuses.some((status) =>
      status.models.some((model) => model.cases.some((entry) => entry.id === selectedId)),
    )
    return (
      <div
        key={nodeId}
        className={clsx(
          'case-tree__node',
          'case-tree__node--level-2',
          containsSelection && 'is-highlighted',
          expanded && 'is-expanded',
        )}
      >
        <button type="button" className="case-tree__toggle" onClick={() => toggleNode(nodeId)} aria-expanded={expanded}>
          <span>{algorithm.label}</span>
          <span className="case-tree__count">{algorithm.count}</span>
        </button>
        {expanded && (
          <div className="case-tree__children">
            {algorithm.statuses.map((status) => renderStatusBranch(status, nodeId))}
          </div>
        )}
      </div>
    )
  }, [isNodeExpanded, renderStatusBranch, selectedId, toggleNode])

  const renderCategoryBranch = useCallback((category: ErrorCategoryGroup, prefix: string) => {
    const nodeId = `${prefix}|category:${category.key}`
    const expanded = isNodeExpanded(nodeId)
    const containsSelection = category.algorithms.some((algorithm) =>
      algorithm.statuses.some((status) => status.models.some((model) => model.cases.some((entry) => entry.id === selectedId))),
    )
    return (
      <div
        key={nodeId}
        className={clsx(
          'case-tree__node',
          'case-tree__node--level-1',
          containsSelection && 'is-highlighted',
          expanded && 'is-expanded',
        )}
      >
        <button type="button" className="case-tree__toggle" onClick={() => toggleNode(nodeId)} aria-expanded={expanded}>
          <span>{category.label}</span>
          <span className="case-tree__count">{category.count}</span>
        </button>
        {expanded && (
          <div className="case-tree__children">
            {category.algorithms.map((algorithm) => renderAlgorithmBranch(algorithm, nodeId))}
          </div>
        )}
      </div>
    )
  }, [isNodeExpanded, renderAlgorithmBranch, selectedId, toggleNode])

  const renderLanguageBranch = useCallback((language: LanguageGroup) => {
    const nodeId = `lang:${language.key}`
    const expanded = isNodeExpanded(nodeId)
    const containsSelection = language.categories.some((category) =>
      category.algorithms.some((algorithm) =>
        algorithm.statuses.some((status) => status.models.some((model) => model.cases.some((entry) => entry.id === selectedId))),
      ),
    )
    return (
      <div
        key={nodeId}
        className={clsx(
          'case-tree__node',
          'case-tree__node--level-0',
          containsSelection && 'is-highlighted',
          expanded && 'is-expanded',
        )}
      >
        <button type="button" className="case-tree__toggle" onClick={() => toggleNode(nodeId)} aria-expanded={expanded}>
          <span>{language.label}</span>
          <span className="case-tree__count">{language.count}</span>
        </button>
        {expanded && (
          <div className="case-tree__children">
            {language.categories.map((category) => renderCategoryBranch(category, nodeId))}
          </div>
        )}
      </div>
    )
  }, [isNodeExpanded, renderCategoryBranch, selectedId, toggleNode])

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div>
          <p className="sidebar__eyebrow">Dataset</p>
          <h2>{suiteLabel}</h2>
        </div>
        <div className="sidebar__header-controls">
          <span className="sidebar__count" title={`${filteredCount} of ${totalCount} cases visible`}>
            {filterActive ? `${filteredCount}/${totalCount}` : totalCount}
          </span>
          <Button
            size="small"
            variant="outlined"
            onClick={() => {
              void onRefreshDataset()
            }}
            disabled={datasetRefreshing}
            sx={{ textTransform: 'none', whiteSpace: 'nowrap' }}
          >
            {datasetRefreshing ? 'Refreshing…' : 'Reload data'}
          </Button>
        </div>
      </div>
      {datasetRefreshError && <p className="sidebar__status sidebar__status--error sidebar__status--compact">{datasetRefreshError}</p>}
      <div className="sidebar__filters-card">
        <div className="sidebar__quick-search">
          <TextField
            label="Quick Search"
            placeholder="Fingerprint (prefix ok)"
            variant="filled"
            size="small"
            value={filters.fingerprintQuery}
            onChange={(event) => onSetFingerprintQuery(event.target.value)}
            inputProps={{ spellCheck: false }}
            sx={{
              flex: 1,
              '& .MuiFilledInput-root': {
                borderRadius: '0.75rem',
                backgroundColor: 'rgba(255, 255, 255, 0.04)',
                color: '#f6fbff',
              },
              '& .MuiFilledInput-root:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
              },
              '& .MuiFilledInput-root.Mui-focused': {
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
              },
              '& .MuiInputLabel-root': {
                color: 'var(--color-text-dim)',
              },
              '& .MuiInputLabel-root.Mui-focused': {
                color: 'var(--color-accent)',
              },
              '& .MuiFilledInput-input': {
                color: '#fefefe',
              },
            }}
          />
          <Tooltip title={advancedOpen ? 'Hide advanced filters' : 'Show advanced filters'} placement="top">
            <Badge
              variant="dot"
              color="info"
              invisible={!advancedFiltersActive}
              sx={{
                '& .MuiBadge-badge': {
                  backgroundColor: 'var(--color-accent)',
                },
              }}
            >
              <IconButton
                aria-label={advancedOpen ? 'Hide advanced filters' : 'Show advanced filters'}
                aria-pressed={advancedOpen}
                onClick={toggleAdvanced}
                size="small"
                sx={{
                  alignSelf: 'stretch',
                  borderRadius: '0.75rem',
                  border: '1px solid var(--color-border)',
                  backgroundColor: advancedOpen ? 'rgba(92, 200, 255, 0.14)' : 'rgba(255, 255, 255, 0.02)',
                  color: advancedFiltersActive ? 'var(--color-accent)' : 'var(--color-text-dim)',
                  '&:hover': {
                    backgroundColor: 'rgba(92, 200, 255, 0.10)',
                  },
                }}
              >
                <FilterListIcon fontSize="small" />
              </IconButton>
            </Badge>
          </Tooltip>
        </div>

        <Collapse in={advancedOpen} timeout={180} unmountOnExit>
          <Divider className="sidebar__filters-divider" sx={{ marginTop: '0.85rem' }} />
          <div className="sidebar__filters-header" style={{ marginTop: '0.85rem' }}>
            <div>
              <p className="sidebar__eyebrow sidebar__eyebrow--compact">Advanced filters</p>
              <Typography variant="body2" sx={{ color: 'var(--color-text-dim)' }}>
                {filterActive ? `${filteredCount} results` : 'Showing all cases'}
              </Typography>
            </div>
            <Button
              size="small"
              variant="text"
              color="inherit"
              disabled={!filterActive}
              onClick={onClearFilters}
              sx={{
                color: filterActive ? 'var(--color-accent)' : 'var(--color-text-dim)',
                minWidth: 0,
                textTransform: 'none',
              }}
            >
              Clear all
            </Button>
          </div>

          <div className="sidebar__filters-grid">
          <FilterMultiSelect
            label="Language"
            placeholder="All languages"
            options={languageOptions}
            values={filters.languages}
            onChange={(values) => onSetFilterValues('languages', values)}
          />
          <FilterMultiSelect
            label="First-error type"
            placeholder="All error types"
            options={errorCategoryOptions}
            values={filters.errorCategories}
            onChange={(values) => onSetFilterValues('errorCategories', values)}
          />
          <FilterMultiSelect
            label="Model"
            placeholder="All models"
            options={modelOptions}
            values={filters.models}
            onChange={(values) => onSetFilterValues('models', values)}
          />
          <FilterMultiSelect
            label="Algorithm"
            placeholder="All algorithms"
            options={algorithmOptions}
            values={filters.algorithms}
            onChange={(values) => onSetFilterValues('algorithms', values)}
          />
          <FilterMultiSelect
            label="Status"
            placeholder="All statuses"
            options={statusOptions}
            values={filters.statuses}
            onChange={(values) => onSetFilterValues('statuses', values)}
          />
          </div>
        </Collapse>
      </div>
      {loading && !cases.length && <p className="sidebar__status">Loading…</p>}
      {error && <p className="sidebar__status sidebar__status--error">{error}</p>}
      {!loading && !cases.length ? (
        <p className="sidebar__status">No cases match your filters.</p>
      ) : (
        <div className="case-tree" role="tree">
          {caseTree.map((language) => renderLanguageBranch(language))}
        </div>
      )}
    </aside>
  )
}

interface StatusChipProps {
  label?: string
  value: AnnotationState['sourceQuality']
}

function StatusChip({ label, value }: StatusChipProps) {
  if (!value) {
    return (
      <span className="chip chip--unset">
        {label && <strong>{label}: </strong>}
        Pending
      </span>
    )
  }
  return (
    <span className={clsx('chip', value === 'good' ? 'chip--good' : 'chip--poor')}>
      {label && <strong>{label}: </strong>}
      {value === 'good' ? 'Good' : 'Poor'}
    </span>
  )
}

interface OutcomeChipProps {
  value: AnnotationState['finalOutcome']
}

function OutcomeChip({ value }: OutcomeChipProps) {
  if (value === 'pending') {
    return <span className="chip chip--pending">Pending</span>
  }
  return (
    <span className={clsx('chip', value === 'good' ? 'chip--good' : 'chip--bad')}>
      Final: {value === 'good' ? 'Good' : 'Bad'}
    </span>
  )
}

function PatchChip({ applied, success }: { applied: boolean; success: boolean }) {
  if (success) {
    return <span className="chip chip--good">Success</span>
  }
  if (applied) {
    return <span className="chip chip--pending">Applied</span>
  }
  return <span className="chip chip--poor">Failed</span>
}

interface FilterOption {
  value: string
  label: string
  count: number
}

interface FilterMultiSelectProps {
  label: string
  placeholder: string
  options: FilterOption[]
  values: string[]
  onChange: (values: string[]) => void
}

function FilterMultiSelect({ label, placeholder, options, values, onChange }: FilterMultiSelectProps) {
  const selected = useMemo(() => options.filter((option) => values.includes(option.value)), [options, values])
  return (
    <Autocomplete
      multiple
      size="small"
      disableCloseOnSelect
      options={options}
      value={selected}
      getOptionLabel={(option) => option.label}
      isOptionEqualToValue={(option, value) => option.value === value.value}
      onChange={(_, next) => onChange(next.map((option) => option.value))}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          placeholder={placeholder}
          variant="filled"
          size="small"
        />
      )}
      renderTags={(tagValue, getTagProps) =>
        tagValue.map((option, index) => (
          <Chip
            {...getTagProps({ index })}
            key={option.value}
            label={option.label}
            size="small"
            variant="filled"
            sx={{
              borderRadius: '999px',
              backgroundColor: 'rgba(92, 200, 255, 0.2)',
              color: '#f6fbff',
            }}
          />
        ))
      }
      renderOption={(props, option, { selected: isSelected }) => (
        <li {...props} key={option.value}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              width: '100%',
              alignItems: 'center',
              color: '#eef6ff',
            }}
          >
            <Typography variant="body2" sx={{ color: '#eef6ff' }}>
              {option.label}
            </Typography>
            <Chip
              label={option.count}
              size="small"
              variant={isSelected ? 'filled' : 'outlined'}
              sx={{
                borderRadius: '999px',
                borderColor: 'rgba(255,255,255,0.3)',
                backgroundColor: isSelected ? 'rgba(92, 200, 255, 0.3)' : 'transparent',
                color: '#eef6ff',
              }}
            />
          </Box>
        </li>
      )}
      sx={{
        width: '100%',
        '& .MuiFilledInput-root': {
          borderRadius: '0.75rem',
          backgroundColor: 'rgba(255, 255, 255, 0.04)',
          color: '#f6fbff',
        },
        '& .MuiFilledInput-root:hover': {
          backgroundColor: 'rgba(255, 255, 255, 0.06)',
        },
        '& .MuiFilledInput-root.Mui-focused': {
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
        },
        '& .MuiInputLabel-root': {
          color: 'var(--color-text-dim)',
        },
        '& .MuiInputLabel-root.Mui-focused': {
          color: 'var(--color-accent)',
        },
        '& .MuiFilledInput-input': {
          color: '#fefefe',
        },
        '& .MuiChip-root': {
          backgroundColor: 'rgba(92, 200, 255, 0.25)',
          color: '#f6fbff',
          borderRadius: '999px',
        },
      }}
      slotProps={{
        paper: {
          sx: {
            backgroundColor: 'rgba(5, 6, 10, 0.96)',
            border: '1px solid var(--color-border)',
            color: '#eef6ff',
          },
        },
        listbox: {
          sx: {
            '& li.MuiAutocomplete-option': {
              fontSize: '0.85rem',
              color: '#eef6ff',
            },
            '& li.MuiAutocomplete-option.Mui-focused': {
              backgroundColor: 'rgba(92, 200, 255, 0.18)',
            },
            '& li.MuiAutocomplete-option[aria-selected="true"]': {
              backgroundColor: 'rgba(92, 200, 255, 0.25)',
            },
          },
        },
      }}
    />
  )
}

function buildFilterOptions(cases: CaseSummary[], valueGetter: (testCase: CaseSummary) => string) {
  const counts = new Map<string, number>()
  for (const testCase of cases) {
    const value = valueGetter(testCase)
    if (!value) continue
    counts.set(value, (counts.get(value) ?? 0) + 1)
  }
  return Array.from(counts.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([value, count]) => ({ value, label: value, count }))
}

function buildStatusOptions(cases: CaseSummary[]): FilterOption[] {
  const counts: Record<string, number> = {}
  for (const testCase of cases) {
    const status = deriveCaseStatus(testCase)
    counts[status] = (counts[status] ?? 0) + 1
  }
  return CASE_STATUS_OPTIONS.map((option) => ({
    value: option.value,
    label: option.label,
    count: counts[option.value] ?? 0,
  }))
}

function buildErrorCategoryOptions(cases: CaseSummary[]): FilterOption[] {
  const counts: Record<string, number> = {}
  for (const testCase of cases) {
    const key = testCase.firstErrorCategory == null ? 'unlabeled' : String(testCase.firstErrorCategory)
    counts[key] = (counts[key] ?? 0) + 1
  }

  const keys = Object.keys(counts)
  keys.sort((a, b) => {
    if (a === 'unlabeled') return 1
    if (b === 'unlabeled') return -1
    const ai = Number.parseInt(a, 10)
    const bi = Number.parseInt(b, 10)
    if (Number.isFinite(ai) && Number.isFinite(bi)) return ai - bi
    return a.localeCompare(b)
  })

  return keys.map((key) => ({
    value: key,
    label: formatFirstErrorCategoryLabel(key),
    count: counts[key] ?? 0,
  }))
}

function buildCaseTree(cases: CaseSummary[]): LanguageGroup[] {
  const languageMap = new Map<string, LanguageBuilder>()
  for (const testCase of cases) {
    const languageKey = testCase.language || 'Unknown Language'
    const categoryKey = testCase.firstErrorCategory == null ? 'unlabeled' : String(testCase.firstErrorCategory)
    const algorithmKey = testCase.algorithm || 'Unknown Algorithm'
    const statusKey = deriveCaseStatus(testCase)
    const modelKey = testCase.modelSlug || 'Unknown Model'

    if (!languageMap.has(languageKey)) {
      languageMap.set(languageKey, {
        key: languageKey,
        label: languageKey,
        count: 0,
        categories: new Map(),
      })
    }
    const languageNode = languageMap.get(languageKey)!
    languageNode.count += 1

    if (!languageNode.categories.has(categoryKey)) {
      languageNode.categories.set(categoryKey, {
        key: categoryKey,
        label: formatFirstErrorCategoryLabel(categoryKey),
        count: 0,
        algorithms: new Map(),
      })
    }
    const categoryNode = languageNode.categories.get(categoryKey)!
    categoryNode.count += 1

    if (!categoryNode.algorithms.has(algorithmKey)) {
      categoryNode.algorithms.set(algorithmKey, {
        key: algorithmKey,
        label: algorithmKey,
        count: 0,
        statuses: new Map(),
      })
    }
    const algorithmNode = categoryNode.algorithms.get(algorithmKey)!
    algorithmNode.count += 1

    if (!algorithmNode.statuses.has(statusKey)) {
      algorithmNode.statuses.set(statusKey, {
        key: statusKey,
        label: CASE_STATUS_OPTIONS.find((option) => option.value === statusKey)?.label ?? statusKey,
        count: 0,
        models: new Map(),
      })
    }
    const statusNode = algorithmNode.statuses.get(statusKey)!
    statusNode.count += 1

    if (!statusNode.models.has(modelKey)) {
      statusNode.models.set(modelKey, {
        key: modelKey,
        label: modelKey,
        count: 0,
        cases: [],
      })
    }
    const modelNode = statusNode.models.get(modelKey)!
    modelNode.count += 1
    modelNode.cases.push(testCase)
  }

  return Array.from(languageMap.values())
    .sort((a, b) => a.label.localeCompare(b.label))
    .map((language) => ({
      key: language.key,
      label: language.label,
      count: language.count,
      categories: Array.from(language.categories.values())
        .sort((a, b) => {
          if (a.key === 'unlabeled') return 1
          if (b.key === 'unlabeled') return -1
          const ai = Number.parseInt(a.key, 10)
          const bi = Number.parseInt(b.key, 10)
          if (Number.isFinite(ai) && Number.isFinite(bi)) return ai - bi
          return a.label.localeCompare(b.label)
        })
        .map((category) => ({
          key: category.key,
          label: category.label,
          count: category.count,
          algorithms: Array.from(category.algorithms.values())
            .sort((a, b) => a.label.localeCompare(b.label))
            .map((algorithm) => ({
              key: algorithm.key,
              label: algorithm.label,
              count: algorithm.count,
              statuses: Array.from(algorithm.statuses.values())
                .sort((a, b) => statusOrder(a.key) - statusOrder(b.key))
                .map((status) => ({
                  key: status.key,
                  label: status.label,
                  count: status.count,
                  models: Array.from(status.models.values())
                    .sort((a, b) => a.label.localeCompare(b.label))
                    .map((model) => ({
                      key: model.key,
                      label: model.label,
                      count: model.count,
                      cases: [...model.cases].sort((aCase, bCase) => aCase.filePath.localeCompare(bCase.filePath)),
                    })),
                })),
            })),
        })),
    }))
}

function statusOrder(value: CaseStatusFilter): number {
  const index = CASE_STATUS_OPTIONS.findIndex((option) => option.value === value)
  return index === -1 ? CASE_STATUS_OPTIONS.length : index
}

interface LanguageBuilder {
  key: string
  label: string
  count: number
  categories: Map<string, ErrorCategoryBuilder>
}

interface ErrorCategoryBuilder {
  key: string
  label: string
  count: number
  algorithms: Map<string, AlgorithmBuilder>
}

interface AlgorithmBuilder {
  key: string
  label: string
  count: number
  statuses: Map<CaseStatusFilter, StatusBuilder>
}

interface StatusBuilder {
  key: CaseStatusFilter
  label: string
  count: number
  models: Map<string, ModelBuilder>
}

interface ModelBuilder {
  key: string
  label: string
  count: number
  cases: CaseSummary[]
}
