export function formatNumber(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value);
}
