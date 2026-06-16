import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HttpClient, provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import {
  authInterceptor,
  OidcSecurityService,
  provideAuth,
  StsConfigHttpLoader,
  StsConfigLoader,
} from 'angular-auth-oidc-client';
import { firstValueFrom, map } from 'rxjs';

import { routes } from './app.routes';
import { AppConfig, ConfigService } from './core/config.service';

export const httpLoaderFactory = (http: HttpClient): StsConfigHttpLoader => {
  const config$ = http.get<AppConfig>('/config.json').pipe(
    map((cfg) => ({
      authority: cfg.auth.authority,
      redirectUrl: window.location.origin,
      postLogoutRedirectUri: window.location.origin,
      clientId: cfg.auth.clientId,
      scope: cfg.auth.scope,
      responseType: 'code',
      silentRenew: true,
      useRefreshToken: true,
      secureRoutes: [cfg.apiUrl],
    })),
  );
  return new StsConfigHttpLoader(config$);
};

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideAnimationsAsync(),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor()])),
    provideAppInitializer(() => inject(ConfigService).load()),
    provideAuth({
      loader: {
        provide: StsConfigLoader,
        useFactory: httpLoaderFactory,
        deps: [HttpClient],
      },
    }),
    provideAppInitializer(async () => {
      const oidc = inject(OidcSecurityService);
      const http = inject(HttpClient);
      const config = inject(ConfigService);
      // Other initializers run concurrently, so apiUrl() isn't guaranteed to be
      // set yet — load() is idempotent, so this just guarantees it's ready.
      await config.load();

      const ensureUserCreated = () => firstValueFrom(http.get(`${config.apiUrl()}/users/me`));

      try {
        const { isAuthenticated } = await firstValueFrom(oidc.checkAuth());
        if (isAuthenticated) {
          await ensureUserCreated();
        } else {
          oidc.authorize();
          await firstValueFrom(oidc.stsCallback$);
          await ensureUserCreated();
        }
      } catch {
        // Auth/user-creation failures shouldn't block app bootstrap.
      }
    }),
  ],
};
