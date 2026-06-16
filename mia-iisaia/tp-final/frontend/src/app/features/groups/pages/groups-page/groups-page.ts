import { Component, inject, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { Group, GroupsService, UserPublic } from '../../groups.service';
import { GroupCardComponent } from '../../components/group-card/group-card';

@Component({
  selector: 'app-groups-page',
  imports: [
    GroupCardComponent,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './groups-page.html',
  styleUrl: './groups-page.scss',
})
export class GroupsPage {
  private readonly groupsService = inject(GroupsService);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly authenticated = this.oidc.authenticated;

  protected readonly groups = httpResource<Group[]>(() =>
    this.authenticated().isAuthenticated ? `${this.config.apiUrl()}/groups` : undefined,
  );

  protected readonly allUsers = httpResource<UserPublic[]>(() =>
    this.authenticated().isAuthenticated ? `${this.config.apiUrl()}/users` : undefined,
  );

  protected readonly showCreateForm = signal(false);
  protected readonly newGroupName = signal('');
  protected readonly isCreating = signal(false);

  protected createGroup(): void {
    const name = this.newGroupName().trim();
    if (!name) return;
    this.isCreating.set(true);
    this.groupsService.createGroup(name).subscribe({
      next: () => {
        this.newGroupName.set('');
        this.showCreateForm.set(false);
        this.isCreating.set(false);
        this.groups.reload();
      },
      error: () => this.isCreating.set(false),
    });
  }

  protected onGroupMutated(): void {
    this.groups.reload();
  }
}
