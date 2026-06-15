import { of } from 'rxjs';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { PortalPage } from './portal-page';

const unauthenticatedOidc = {
  authenticated: signal({ isAuthenticated: false }),
};

const authenticatedOidc = {
  authenticated: signal({ isAuthenticated: true }),
  logoff: () => of(null),
};

describe('PortalPage — unauthenticated', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortalPage],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: unauthenticatedOidc },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(PortalPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders no logout button when unauthenticated', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    const buttons = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button'));
    expect(buttons.some((b) => b.textContent?.trim() === 'Logout')).toBe(false);
  });
});

describe('PortalPage — authenticated', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortalPage],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: authenticatedOidc },
      ],
    }).compileComponents();
  });

  it('shows a logout button when authenticated', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    const buttons = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button'));
    expect(buttons.some((b) => b.textContent?.trim() === 'Logout')).toBe(true);
  });
});
