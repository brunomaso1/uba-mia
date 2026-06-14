import { TestBed } from '@angular/core/testing';
import { ConfigService } from './config.service';

describe('ConfigService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads config.json and exposes apiUrl', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ apiUrl: 'http://test-host:9999' }),
      }),
    );

    const service = TestBed.inject(ConfigService);
    await service.load();

    expect(service.apiUrl()).toBe('http://test-host:9999');
  });

  it('rejects when config.json fetch is not ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    const service = TestBed.inject(ConfigService);

    await expect(service.load()).rejects.toThrow();
  });

  it('returns empty apiUrl before load', () => {
    const service = TestBed.inject(ConfigService);
    expect(service.apiUrl()).toBe('');
  });
});
