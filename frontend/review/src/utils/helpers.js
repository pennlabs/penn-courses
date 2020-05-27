import { DEFAULT_COLUMNS } from '../constants'

export const capitalize = str =>
  str.replace(/(?:^|\s)\S/g, e => e.toUpperCase())

export function orderColumns(cols) {
  const colSet = new Set(cols)
  const fixedCols = [
    'latest_semester',
    'num_semesters',
    ...DEFAULT_COLUMNS,
  ].filter(a => colSet.has(a))
  const fixedColsSet = new Set(fixedCols)
  return fixedCols.concat(cols.filter(a => !fixedColsSet.has(a)).sort())
}

export function getColumnName(key) {
  return key
    .substring(1)
    .split(/(?=[A-Z])/)
    .join(' ')
    .replace('T A', 'TA')
    .replace(/Recommend/g, 'Rec.')
}

// Monotonically maps semesters to integer values - later semesters have higher numbers.
export function convertSemesterToInt(sem) {
  if (!(typeof sem === 'string' || sem)) return 0
  const [season = 'Spring', year = '0'] = sem.split(' ')
  return parseInt(year) * 3 + { Spring: 0, Summer: 1, Fall: 2 }[season]
}

// Compares PCR semester codes, sorting the most recent semester first.
export function compareSemesters(a, b) {
  return convertSemesterToInt(b) - convertSemesterToInt(a)
}

// Converts an instructor name into a unique key that should be the same for historical data and the Penn directory.
// TODO: Move this to a Redux store or React context
// Another idea: move to localstorage so cache persists between sessions!
const nameCache = {}

export function convertInstructorName(name) {
  if (name in nameCache) {
    return nameCache[name]
  }
  const out = name
    .toUpperCase()
    .substr(0, 30)
    .replace(/[^a-zA-Z\s]/g, '')
    .replace(/ [A-Z]+ /g, ' ')
  nameCache[name] = out
  return out
}

export const getCartCourses = () =>
  Object.keys(localStorage)
    .filter(k => !k.startsWith('meta-'))
    .map(k => {
      const out = JSON.parse(localStorage.getItem(k))
      if (typeof out !== 'object') {
        return null
      }
      const typeDict = {}
      if (typeof out.info !== 'undefined') {
        out.info.forEach(v => {
          typeDict[v.category] = v
        })
        out.info = typeDict
      }
      out.course = k
      return out
    })
    .filter(a => a !== null)
