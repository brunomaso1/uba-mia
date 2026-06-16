import { Component, inject, input, output, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { Group, GroupsService, UserPublic } from '../../groups.service';
import { AddMemberFormComponent } from '../add-member-form/add-member-form';

@Component({
  selector: 'app-group-card',
  imports: [
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    AddMemberFormComponent,
  ],
  templateUrl: './group-card.html',
  styleUrl: './group-card.scss',
})
export class GroupCardComponent {
  private readonly groupsService = inject(GroupsService);
  private readonly router = inject(Router);

  readonly group = input.required<Group>();
  readonly allUsers = input<UserPublic[]>([]);

  readonly renamed = output<Group>();
  readonly deleted = output<void>();
  readonly memberAdded = output<void>();

  protected readonly isEditing = signal(false);
  protected readonly editName = signal('');
  protected readonly showAddMember = signal(false);
  protected readonly isSaving = signal(false);

  protected startEdit(): void {
    this.editName.set(this.group().name);
    this.isEditing.set(true);
  }

  protected cancelEdit(): void {
    this.isEditing.set(false);
  }

  protected confirmRename(): void {
    const name = this.editName().trim();
    if (!name || name === this.group().name) {
      this.isEditing.set(false);
      return;
    }
    this.isSaving.set(true);
    this.groupsService.renameGroup(this.group().id, name).subscribe({
      next: (updated) => {
        this.renamed.emit(updated);
        this.isEditing.set(false);
        this.isSaving.set(false);
      },
      error: () => this.isSaving.set(false),
    });
  }

  protected onDelete(): void {
    this.isSaving.set(true);
    this.groupsService.deleteGroup(this.group().id).subscribe({
      next: () => this.deleted.emit(),
      error: () => this.isSaving.set(false),
    });
  }

  protected goToDetail(): void {
    this.router.navigate(['/groups', this.group().id]);
  }

  protected onMemberAdded(): void {
    this.showAddMember.set(false);
    this.memberAdded.emit();
  }
}
