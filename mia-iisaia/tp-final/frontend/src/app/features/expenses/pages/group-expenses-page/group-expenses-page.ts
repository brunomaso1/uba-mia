import { Component, computed, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { Expense } from '../../expenses.service';
import { ExpenseFormDialogComponent } from '../../components/expense-form-dialog/expense-form-dialog';

@Component({
  selector: 'app-group-expenses-page',
  imports: [MatButtonModule, MatIconModule, MatListModule, MatProgressSpinnerModule],
  templateUrl: './group-expenses-page.html',
  styleUrl: './group-expenses-page.scss',
})
export class GroupExpensesPage {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);
  private readonly dialog = inject(MatDialog);

  protected readonly groupId = toSignal(this.route.paramMap.pipe(map((p) => p.get('id') ?? '')), {
    initialValue: '',
  });

  private readonly isAuthenticated = computed(() => this.oidc.authenticated().isAuthenticated);

  protected readonly expenses = httpResource<Expense[]>(() =>
    this.isAuthenticated() && this.groupId()
      ? `${this.config.apiUrl()}/groups/${this.groupId()}/expenses`
      : undefined,
  );

  protected goBack(): void {
    this.router.navigate(['/groups']);
  }

  protected openAddExpenseDialog(): void {
    const ref = this.dialog.open(ExpenseFormDialogComponent, {
      data: { preselectedGroupId: this.groupId() },
    });
    ref.afterClosed().subscribe((result: unknown) => {
      if (result) this.expenses.reload();
    });
  }
}
