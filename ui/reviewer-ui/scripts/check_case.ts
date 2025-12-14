import { DatasetLoader } from '../src/server/datasetLoader'

async function main() {
  const loader = new DatasetLoader('../../benchmarks/generated')
  await loader.ensureLoaded()
  const id = process.argv[2]
  if (!id) {
    console.error('usage: tsx scripts/check_case.ts <case-id>')
    process.exit(1)
  }
  const detail = await loader.getDetail(id)
  if (!detail) {
    console.error('Case not found')
    process.exit(1)
  }
  console.log('case:', detail.summary.caseId)
  console.log('run:', detail.summary.runId)
  console.log('model:', detail.summary.modelSlug)
  console.log('algorithm:', detail.summary.algorithm)
  console.log('before length:', detail.before.length)
  console.log('after length:', detail.after.length)
  console.log('diff length:', detail.diff.length)
  console.log('afterSource:', detail.derived.afterSource)
  console.log('patchApplied:', detail.summary.patchApplied)
  console.log('success:', detail.summary.success)
  console.log('before === after ?', detail.before === detail.after)
  console.log('after snippet:\n', detail.after.slice(0, 200))
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
