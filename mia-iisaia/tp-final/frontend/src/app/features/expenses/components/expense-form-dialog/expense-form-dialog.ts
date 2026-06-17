// frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.ts
import { Component, effect, inject, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { ConfigService } from '../../../../core/config.service';
import { Expense, ExpensesService } from '../../expenses.service';
import { Group } from '../../../groups/groups.service';

export interface ExpenseFormDialogData {
  preselectedGroupId?: string;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

@Component({
  selector: 'app-expense-form-dialog',
  imports: [MatButtonModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatSelectModule],
  templateUrl: './expense-form-dialog.html',
  styleUrl: './expense-form-dialog.scss',
})
export class ExpenseFormDialogComponent {
  private readonly config = inject(ConfigService);
  private readonly expensesService = inject(ExpensesService);
  private readonly dialogRef = inject(
    MatDialogRef<ExpenseFormDialogComponent, Expense | undefined>,
  );
  private readonly data = inject<ExpenseFormDialogData | null>(MAT_DIALOG_DATA, { optional: true });

  protected readonly groups = httpResource<Group[]>(() => `${this.config.apiUrl()}/groups`);

  protected readonly description = signal('');
  protected readonly amount = signal<number | null>(null);
  protected readonly date = signal(todayIsoDate());
  protected readonly selectedGroupId = signal<string | null>(null);
  protected readonly isSubmitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  constructor() {
    effect(() => {
      const groups = this.groups.value();
      if (!groups || groups.length === 0 || this.selectedGroupId()) return;
      const preselected = this.data?.preselectedGroupId;
      const match = preselected && groups.some((g) => g.id === preselected);
      this.selectedGroupId.set(match ? (preselected as string) : groups[0].id);
    });
  }

  protected onSubmit(): void {
    const groupId = this.selectedGroupId();
    const amountValue = this.amount();
    const dateValue = this.date();
    if (!groupId || amountValue === null || amountValue <= 0 || !dateValue) return;

    this.isSubmitting.set(true);
    this.errorMessage.set(null);
    this.expensesService
      .createExpense(groupId, {
        description: this.description().trim() || null,
        amount: amountValue.toFixed(2),
        date: dateValue,
      })
      .subscribe({
        next: (expense) => {
          this.isSubmitting.set(false);
          this.dialogRef.close(expense);
        },
        error: () => {
          this.isSubmitting.set(false);
          this.errorMessage.set('No se pudo registrar el gasto. Intentá nuevamente.');
        },
      });
  }

  protected onCancel(): void {
    this.dialogRef.close(undefined);
  }
}
