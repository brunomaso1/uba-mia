import { Component, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { MatButtonModule } from '@angular/material/button';
import { ConfigService } from '../../../../core/config.service';
import { UserCardComponent } from '../../components/user-card/user-card';

@Component({
  selector: 'app-portal-page',
  imports: [MatButtonModule, UserCardComponent],
  templateUrl: './portal-page.html',
  styleUrl: './portal-page.scss',
})
export class PortalPage {
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly authenticated = this.oidc.authenticated;

  protected readonly me = httpResource<unknown>(() =>
    this.authenticated().isAuthenticated ? `${this.config.apiUrl()}/users/me` : undefined,
  );

  protected logout(): void {
    this.oidc.logoff().subscribe();
  }
}
