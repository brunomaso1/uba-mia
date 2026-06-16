import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { GroupDetailPage } from './group-detail-page';
import { ConfigService } from '../../../../core/config.service';

describe('GroupDetailPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupDetailPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
        {
          provide: OidcSecurityService,
          useValue: {
            authenticated: signal({ isAuthenticated: true }),
          },
        },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(GroupDetailPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows page heading', () => {
    const fixture = TestBed.createComponent(GroupDetailPage);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent).toContain(
      'Miembros del grupo',
    );
  });
});
