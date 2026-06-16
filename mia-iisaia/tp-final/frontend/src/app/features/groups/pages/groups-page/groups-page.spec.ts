import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { GroupsPage } from './groups-page';
import { GroupsService } from '../../groups.service';
import { ConfigService } from '../../../../core/config.service';

describe('GroupsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupsPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: GroupsService,
          useValue: {
            createGroup: () => of({ id: 'g-1', name: 'New', member_count: 1 }),
            renameGroup: () => of({}),
            deleteGroup: () => of(undefined),
            addMember: () => of(undefined),
          },
        },
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
    const fixture = TestBed.createComponent(GroupsPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows page heading', () => {
    const fixture = TestBed.createComponent(GroupsPage);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('h1')?.textContent).toContain(
      'Mis Grupos',
    );
  });
});
