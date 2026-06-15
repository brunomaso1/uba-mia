import { of } from 'rxjs';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { App } from './app';

const unauthenticatedOidc = {
  authenticated: signal({ isAuthenticated: false }),
};

const authenticatedOidc = {
  authenticated: signal({ isAuthenticated: true }),
  logoff: () => of(null),
};

describe('App — unauthenticated state', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: unauthenticatedOidc },
      ],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should render the config check heading', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Runtime config check');
  });

  it('does not render a login button', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const buttons = Array.from(compiled.querySelectorAll('button'));
    expect(buttons.every((b) => !b.textContent?.includes('Login'))).toBe(true);
  });
});

describe('App — authenticated state', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: authenticatedOidc },
      ],
    }).compileComponents();
  });

  it('shows a logout button when authenticated', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const buttons = Array.from(compiled.querySelectorAll('button'));
    expect(buttons.some((b) => b.textContent?.includes('Logout'))).toBe(true);
  });
});
