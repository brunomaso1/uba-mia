import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

import { ExpenseFormDialogComponent } from '../../../expenses/components/expense-form-dialog/expense-form-dialog';

@Component({
  selector: 'app-portal-page',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './portal-page.html',
  styleUrl: './portal-page.scss',
})
export class PortalPage {
  private readonly dialog = inject(MatDialog);

  protected openAddExpenseDialog(): void {
    this.dialog.open(ExpenseFormDialogComponent);
  }
}
