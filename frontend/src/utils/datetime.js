const SHANGHAI_TIME_ZONE = 'Asia/Shanghai'

export function parseUtcLike(input) {
  if (!input) return null
  if (input instanceof Date) return input

  const value = String(input).trim()
  if (!value) return null

  const normalized = value.includes(' ') ? value.replace(' ', 'T') : value
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(normalized)
  const date = new Date(hasTimezone ? normalized : `${normalized}Z`)
  return Number.isNaN(date.getTime()) ? null : date
}

function shanghaiParts(input) {
  const date = parseUtcLike(input)
  if (!date) return null

  const formatter = new Intl.DateTimeFormat('zh-CN', {
    timeZone: SHANGHAI_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })

  const parts = formatter.formatToParts(date)
  return Object.fromEntries(parts.filter((item) => item.type !== 'literal').map((item) => [item.type, item.value]))
}

export function formatShanghaiDateTime(input) {
  const parts = shanghaiParts(input)
  if (!parts) return ''
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`
}

export function formatShanghaiDate(input) {
  const parts = shanghaiParts(input)
  if (!parts) return ''
  return `${parts.year}-${parts.month}-${parts.day}`
}

export function formatShanghaiMonthDayTime(input) {
  const parts = shanghaiParts(input)
  if (!parts) return ''
  return `${parts.month}/${parts.day} ${parts.hour}:${parts.minute}`
}

export function formatShanghaiMonthDayChinese(input) {
  const parts = shanghaiParts(input)
  if (!parts) return ''
  return `${Number(parts.month)}月${Number(parts.day)}日 ${parts.hour}:${parts.minute}`
}

export function formatShanghaiChartLabel(input) {
  const parts = shanghaiParts(input)
  if (!parts) return ''
  return `${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`
}
