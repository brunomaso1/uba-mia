import { Service, computed, signal } from '@angular/core';

export interface AppConfig {
  apiUrl: string;
  auth: {
    authority: string;
    clientId: string;
    scope: string;
  };
}

@Service()
export class ConfigService {
  private readonly _config = signal<AppConfig | null>(null);

  readonly apiUrl = computed(() => this._config()?.apiUrl ?? '');
  readonly authConfig = computed(() => this._config()?.auth ?? null);

  async load(): Promise<void> {
    const response = await fetch('/config.json');
    if (!response.ok) {
      throw new Error(`Failed to load config.json: ${response.status}`);
    }
    this._config.set((await response.json()) as AppConfig);
  }
}
