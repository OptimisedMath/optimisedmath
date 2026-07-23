export function scrollElementClearOfMobileChrome(
  element: HTMLElement,
  extraPadding = 24
): void {
  const rect = element.getBoundingClientRect();
  const vv = window.visualViewport;
  const visibleBottom = vv ? vv.offsetTop + vv.height : window.innerHeight;
  const overflow = rect.bottom - visibleBottom + extraPadding;

  if (overflow > 0) {
    window.scrollBy({ top: overflow, behavior: 'smooth' });
  } else if (rect.top < 0) {
    window.scrollBy({ top: rect.top - extraPadding, behavior: 'smooth' });
  }
}
