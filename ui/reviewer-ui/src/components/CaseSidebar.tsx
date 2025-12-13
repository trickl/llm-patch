import { useMemo } from 'react'
import clsx from 'clsx'
import {
  Autocomplete,
  Box,
  Button,
  Chip,
  Divider,
  TextField,
  Typography,
} from '@mui/material'
import type { AnnotationState, CaseSummary } from '../types'
import { defaultAnnotation } from '../types'
import type { FiltersState, FilterKey } from '../store/useReviewStore'
import { CASE_STATUS_OPTIONS, deriveCaseStatus } from '../utils/caseFilters'

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
  onClearFilters: () => void
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
  onClearFilters,
}: CaseSidebarProps) {
  const suiteLabel = allCases[0]?.problemId ?? 'Test Cases'
  const filterActive =
    filters.languages.length + filters.models.length + filters.algorithms.length + filters.statuses.length > 0
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
  const statusOptions = useMemo(() => buildStatusOptions(allCases), [allCases])

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div>
          <p className="sidebar__eyebrow">Dataset</p>
          <h2>{suiteLabel}</h2>
        </div>
        <span className="sidebar__count" title={`${filteredCount} of ${totalCount} cases visible`}>
          {filterActive ? `${filteredCount}/${totalCount}` : totalCount}
        </span>
      </div>
      <div className="sidebar__filters-card">
        <div className="sidebar__filters-header">
          <div>
            <p className="sidebar__eyebrow sidebar__eyebrow--compact">Filters</p>
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
        <Divider className="sidebar__filters-divider" />
        <div className="sidebar__filters-grid">
          <FilterMultiSelect
            label="Language"
            placeholder="All languages"
            options={languageOptions}
            values={filters.languages}
            onChange={(values) => onSetFilterValues('languages', values)}
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
      </div>
      {loading && !cases.length && <p className="sidebar__status">Loading…</p>}
      {error && <p className="sidebar__status sidebar__status--error">{error}</p>}
      <ul className="sidebar__list">
        {cases.map((testCase) => {
          const active = testCase.id === selectedId
          const annotation = annotations[testCase.id] ?? defaultAnnotation
          return (
            <li key={testCase.id}>
              <button
                type="button"
                className={clsx('sidebar__item', active && 'sidebar__item--active')}
                onClick={() => onSelect(testCase.id)}
              >
                <div className="sidebar__item-main">
                  <div>
                    <span className="sidebar__item-title">{testCase.filePath}</span>
                    <span className="sidebar__item-subtitle">{testCase.modelSlug}</span>
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
        })}
      </ul>
    </aside>
  )
}

interface StatusChipProps {
  label?: string
  value: AnnotationState['sourceQuality']
}

function StatusChip({ label, value }: StatusChipProps) {
  return (
    <span className={clsx('chip', `chip--${value}`)}>
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
