/** A client side hint only: the trimmed name has 1 to 100 characters. The server stays the judge of the rest. */
export function looksLikeAName(name: string): boolean {
  const length = name.trim().length;
  return length >= 1 && length <= 100;
}
