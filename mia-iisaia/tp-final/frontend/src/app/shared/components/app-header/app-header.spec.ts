import { TestBed } from '@angular/core/testing';
import { NavigationEnd, provideRouter, Router } from '@angular/router';
import { signal } from '@angular/core';
import { BehaviorSubject, of } from 'rxjs';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { OverlayContainer } from '@angular/cdk/overlay';
import { AppHeaderComponent } from './app-header';

const mockRouter = {
  events: new BehaviorSubject<unknown>(new NavigationEnd(0, '/', '/')),
  routerState: {
    snapshot: {
      root: {
        firstChild: { firstChild: null, title: 'Portal' },
        title: undefined,
      },
    },
  },
  navigate: () => Promise.resolve(true),
  navigateByUrl: () => Promise.resolve(true),
  createUrlTree: (_commands: unknown[]) => ({ toString: () => '/' }),
  serializeUrl: () => '/',
  isActive: () => false,
  url: '/',
};

let logoffCalled = false;

const mockOidc = {
  userData: signal({
    userData: { preferred_username: 'alice', email: 'alice@example.com' },
    allUserData: [],
  }),
  logoff: () => {
    logoffCalled = true;
    return of(null);
  },
};

describe('AppHeaderComponent', () => {
  let overlayContainer: OverlayContainer;

  beforeEach(async () => {
    logoffCalled = false;
    await TestBed.configureTestingModule({
      imports: [AppHeaderComponent],
      providers: [
        provideRouter([]),
        { provide: Router, useValue: mockRouter },
        { provide: OidcSecurityService, useValue: mockOidc },
      ],
    }).compileComponents();
    overlayContainer = TestBed.inject(OverlayContainer);
  });

  afterEach(() => {
    overlayContainer.ngOnDestroy();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows the active route title in the toolbar', () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Portal');
  });

  it('shows the user initial in the avatar button', () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    const avatar = (fixture.nativeElement as HTMLElement).querySelector('.avatar-initial');
    expect(avatar?.textContent?.trim()).toBe('A');
  });

  it('user dropdown shows email and Cerrar sesión', async () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    const userBtn = (fixture.nativeElement as HTMLElement).querySelector(
      '[aria-label^="Cuenta de"]',
    ) as HTMLButtonElement;
    userBtn.click();
    fixture.detectChanges();
    await fixture.whenStable();
    const overlay = overlayContainer.getContainerElement();
    expect(overlay.textContent).toContain('alice@example.com');
    expect(overlay.textContent).toContain('Cerrar sesión');
  });

  it('clicking Cerrar sesión calls logoff', async () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    const userBtn = (fixture.nativeElement as HTMLElement).querySelector(
      '[aria-label^="Cuenta de"]',
    ) as HTMLButtonElement;
    userBtn.click();
    fixture.detectChanges();
    await fixture.whenStable();
    const cerrarBtn = overlayContainer
      .getContainerElement()
      .querySelector('button[mat-menu-item]') as HTMLButtonElement;
    cerrarBtn.click();
    expect(logoffCalled).toBe(true);
  });
});
