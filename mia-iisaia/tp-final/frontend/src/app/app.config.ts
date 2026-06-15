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
import { of, switchMap } from 'rxjs';
import { map } from 'rxjs';

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
    provideAppInitializer(() => {
      const oidc = inject(OidcSecurityService);
      return oidc.checkAuth().pipe(
        switchMap(({ isAuthenticated }) => {
          if (isAuthenticated) {
            return of(void 0 as void);
          }
          oidc.authorize();
          return oidc.stsCallback$.pipe(map(() => void 0 as void));
        }),
      );
    }),
  ],
};
