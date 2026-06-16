import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

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
});
