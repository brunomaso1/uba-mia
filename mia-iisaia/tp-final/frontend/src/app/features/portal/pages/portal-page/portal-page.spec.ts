import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { PortalPage } from './portal-page';

describe('PortalPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortalPage],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(PortalPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows groups navigation card', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Mis Grupos');
  });

  it('opens the expense dialog when the floating add button is clicked', () => {
    const dialog = { open: vi.fn(() => ({ afterClosed: () => of(undefined) })) };
    TestBed.overrideProvider(MatDialog, { useValue: dialog });

    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();

    const fab = (fixture.nativeElement as HTMLElement).querySelector(
      'button[aria-label="Agregar gasto"]',
    ) as HTMLButtonElement;
    fab.click();

    expect(dialog.open).toHaveBeenCalled();
  });
});
