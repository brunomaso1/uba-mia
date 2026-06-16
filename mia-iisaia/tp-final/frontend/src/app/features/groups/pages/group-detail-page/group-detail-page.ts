import { Component, computed, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { Member } from '../../groups.service';

@Component({
  selector: 'app-group-detail-page',
  imports: [MatButtonModule, MatIconModule, MatListModule, MatProgressSpinnerModule],
  templateUrl: './group-detail-page.html',
  styleUrl: './group-detail-page.scss',
})
export class GroupDetailPage {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  private readonly groupId = toSignal(this.route.paramMap.pipe(map((p) => p.get('id') ?? '')), {
    initialValue: '',
  });

  private readonly isAuthenticated = computed(() => this.oidc.authenticated().isAuthenticated);

  protected readonly members = httpResource<Member[]>(() =>
    this.isAuthenticated() && this.groupId()
      ? `${this.config.apiUrl()}/groups/${this.groupId()}/members`
      : undefined,
  );

  protected goBack(): void {
    this.router.navigate(['/groups']);
  }
}
