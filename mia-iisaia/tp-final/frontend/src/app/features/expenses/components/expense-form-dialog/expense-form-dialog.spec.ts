// frontend/src/app/features/expenses/components/expense-form-dialog/expense-form-dialog.spec.ts
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';

import { ExpenseFormDialogComponent } from './expense-form-dialog';
import { ExpensesService } from '../../expenses.service';
import { ConfigService } from '../../../../core/config.service';

const mockGroups = [
  {
    id: 'g-1',
    name: 'Familia',
    created_by: 'u-1',
    created_at: '2026-01-01T00:00:00Z',
    member_count: 2,
  },
  {
    id: 'g-2',
    name: 'Viaje',
    created_by: 'u-1',
    created_at: '2026-01-02T00:00:00Z',
    member_count: 3,
  },
];

function setup(dialogData: { preselectedGroupId?: string } | null, createResult = of({})) {
  const expensesService = { createExpense: vi.fn(() => createResult) };
  TestBed.configureTestingModule({
    imports: [ExpenseFormDialogComponent],
    providers: [
      provideHttpClient(),
      provideHttpClientTesting(),
      { provide: ExpensesService, useValue: expensesService },
      { provide: ConfigService, useValue: { apiUrl: () => 'http://localhost:8000/api/v1' } },
      { provide: MAT_DIALOG_DATA, useValue: dialogData },
      { provide: MatDialogRef, useValue: { close: vi.fn() } },
    ],
  });
  const fixture = TestBed.createComponent(ExpenseFormDialogComponent);
  return {
    fixture,
    expensesService,
    dialogRef: TestBed.inject(MatDialogRef),
    httpMock: TestBed.inject(HttpTestingController),
  };
}

describe('ExpenseFormDialogComponent', () => {
  it('defaults the date field to today', () => {
    const { fixture, httpMock } = setup(null);
    const today = new Date().toISOString().slice(0, 10);
    expect((fixture.componentInstance as any).date()).toBe(today);
    fixture.detectChanges();
    httpMock.expectOne('http://localhost:8000/api/v1/groups').flush(mockGroups);
  });

  it('preselects the group passed via dialog data once groups load', async () => {
    const { fixture, httpMock } = setup({ preselectedGroupId: 'g-2' });
    fixture.detectChanges();
    httpMock.expectOne('http://localhost:8000/api/v1/groups').flush(mockGroups);
    await fixture.whenStable();
    fixture.detectChanges();
    expect((fixture.componentInstance as any).selectedGroupId()).toBe('g-2');
  });

  it('defaults to the first group when no group is preselected', async () => {
    const { fixture, httpMock } = setup(null);
    fixture.detectChanges();
    httpMock.expectOne('http://localhost:8000/api/v1/groups').flush(mockGroups);
    await fixture.whenStable();
    fixture.detectChanges();
    expect((fixture.componentInstance as any).selectedGroupId()).toBe('g-1');
  });

  it('does not submit when no group is selected', () => {
    const { fixture, expensesService } = setup(null);
    const instance = fixture.componentInstance as any;
    instance.amount.set(10);
    instance.onSubmit();
    expect(expensesService.createExpense).not.toHaveBeenCalled();
  });

  it('submits with the selected group and formatted amount, then closes with the result', () => {
    const created = { id: 'e-1' };
    const { fixture, expensesService, dialogRef } = setup(null, of(created));
    const instance = fixture.componentInstance as any;
    instance.selectedGroupId.set('g-1');
    instance.description.set('Cena');
    instance.amount.set(45);
    instance.date.set('2026-06-10');
    instance.onSubmit();
    expect(expensesService.createExpense).toHaveBeenCalledWith('g-1', {
      description: 'Cena',
      amount: '45.00',
      date: '2026-06-10',
    });
    expect(dialogRef.close).toHaveBeenCalledWith(created);
  });

  it('shows an error message and keeps the dialog open when submission fails', () => {
    const { fixture, dialogRef } = setup(
      null,
      throwError(() => new Error('boom')),
    );
    const instance = fixture.componentInstance as any;
    instance.selectedGroupId.set('g-1');
    instance.amount.set(10);
    instance.onSubmit();
    expect(instance.errorMessage()).toContain('No se pudo registrar el gasto');
    expect(dialogRef.close).not.toHaveBeenCalled();
  });

  it('does not submit when amount is NaN', () => {
    const { fixture, expensesService } = setup(null);
    const instance = fixture.componentInstance as any;
    instance.selectedGroupId.set('g-1');
    instance.amount.set(NaN);
    instance.onSubmit();
    expect(expensesService.createExpense).not.toHaveBeenCalled();
  });
});
