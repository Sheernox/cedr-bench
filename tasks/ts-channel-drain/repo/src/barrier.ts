/** A flush snapshot must not expand when new submissions arrive. */
export async function barrier(promises: readonly Promise<unknown>[]): Promise<void> {
  await Promise.all(promises);
}
