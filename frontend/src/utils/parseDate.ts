export function parseDate(value: string | Date) {
  const date = typeof value === 'string' ? new Date(value) : value;
  return isNaN(date.getTime()) ? null : date;
}
