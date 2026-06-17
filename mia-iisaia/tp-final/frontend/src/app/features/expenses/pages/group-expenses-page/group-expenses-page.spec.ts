import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';
import { convertToParamMap } from '@angular/router';
import { vi } from 'vitest';

import { GroupExpensesPage } from './group-expenses-page';
import { ConfigService } from '../../../../core/config.service';

describe('GroupExpensesPage', () => {
  function setup(dialogResult: unknown = undefined) {
    const dialog = { open: vi.fn(() => ({ afterClosed: () => of(dialogResult) })) };
    TestBed.configureTestingModule({
      imports: [GroupExpensesPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        { provide: MatDialog, useValue: dialog },
        {
          provide: ActivatedRoute,
          useValue: { paramMap: of(convertToParamMap({ id: 'g-1' })) },
        },
        { provide: ConfigService, useValue: { apiUrl: () => 'http://localhost:8000/api/v1' } },
        {
          provide: OidcSecurityService,
          useValue: { authenticated: signal({ isAuthenticated: true }) },
        },
      ],
    });
    const fixture = TestBed.createComponent(GroupExpensesPage);
    return { fixture, dialog };
  }

  it('should create', () => {
    const { fixture } = setup();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows page heading', () => {
    const { fixture } = setup();
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent).toContain(
      'Gastos del grupo',
    );
  });

  it('opens the expense dialog with the current group preselected', () => {
    const { fixture, dialog } = setup();
    fixture.detectChanges();
    (fixture.componentInstance as any).openAddExpenseDialog();
    expect(dialog.open).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ data: { preselectedGroupId: 'g-1' } }),
    );
  });
});
