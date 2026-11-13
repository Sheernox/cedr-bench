/** Injectable boundaries keep autosave independent of wall time and storage. */
export interface Clock {
  now(): number;
  schedule(delayMs: number, callback: () => void): () => void;
}
export interface Write {
  key: string;
  value: string;
  generation: number;
}
export interface Receipt {
  key: string;
  generation: number;
}
export type Sink = (write: Readonly<Write>) => Promise<void>;
export interface Options {
  concurrency: number;
  maxAttempts: number;
  retryMs: number;
  clock: Clock;
}
export interface SubmitOptions { signal?: AbortSignal }
export interface Statistics {
  accepted: number;
  persisted: number;
  failed: number;
  attempts: number;
  active: number;
}
