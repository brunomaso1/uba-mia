import { TestBed } from '@angular/core/testing';
import { NavigationEnd, provideRouter, Router } from '@angular/router';
import { signal } from '@angular/core';
import { BehaviorSubject, of } from 'rxjs';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { AppShell } from './app-shell';

const mockRouter = {
  events: new BehaviorSubject<unknown>(new NavigationEnd(0, '/', '/')),
  routerState: {
    snapshot: {
      root: { firstChild: null, title: '' },
    },
  },
  navigate: () => Promise.resolve(true),
  navigateByUrl: () => Promise.resolve(true),
  createUrlTree: (_commands: unknown[]) => ({ toString: () => '/' }),
  serializeUrl: () => '/',
  isActive: () => false,
  url: '/',
};

const mockOidc = {
  userData: signal({ userData: { preferred_username: 'alice', email: '' }, allUserData: [] }),
  logoff: () => of(null),
};

describe('AppShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppShell],
      providers: [
        provideRouter([]),
        { provide: Router, useValue: mockRouter },
        { provide: OidcSecurityService, useValue: mockOidc },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(AppShell);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders app-header', () => {
    const fixture = TestBed.createComponent(AppShell);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('app-header')).toBeTruthy();
  });

  it('renders router-outlet', () => {
    const fixture = TestBed.createComponent(AppShell);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('router-outlet')).toBeTruthy();
  });
});
