import { Component, computed, inject, input, output, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { GroupsService, Member, UserPublic } from '../../groups.service';

@Component({
  selector: 'app-add-member-form',
  imports: [MatButtonModule, MatFormFieldModule, MatProgressSpinnerModule, MatSelectModule],
  templateUrl: './add-member-form.html',
  styleUrl: './add-member-form.scss',
})
export class AddMemberFormComponent {
  private readonly groupsService = inject(GroupsService);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  readonly groupId = input.required<string>();
  readonly allUsers = input<UserPublic[]>([]);
  readonly memberAdded = output<void>();

  private readonly isAuthenticated = computed(() => this.oidc.authenticated().isAuthenticated);

  protected readonly members = httpResource<Member[]>(() =>
    this.isAuthenticated() ? `${this.config.apiUrl()}/groups/${this.groupId()}/members` : undefined,
  );

  protected readonly availableUsers = computed(() => {
    const memberIds = new Set((this.members.value() ?? []).map((m) => m.user_id));
    return this.allUsers().filter((u) => !memberIds.has(u.id));
  });

  protected readonly selectedUserId = signal<string | null>(null);
  protected readonly isSubmitting = signal(false);

  protected onSubmit(): void {
    const userId = this.selectedUserId();
    if (!userId) return;
    this.isSubmitting.set(true);
    this.groupsService.addMember(this.groupId(), userId).subscribe({
      next: () => {
        this.selectedUserId.set(null);
        this.isSubmitting.set(false);
        this.memberAdded.emit();
      },
      error: () => this.isSubmitting.set(false),
    });
  }
}
