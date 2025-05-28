export type Mode = 'AI' | 'WebSearch' | 'Transcription' | 'OFFLINE';

export interface StatusResponse {
  mode: Mode;
  transcription: string;
  response: string;
}