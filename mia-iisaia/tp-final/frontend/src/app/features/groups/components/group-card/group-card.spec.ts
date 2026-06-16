import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { GroupCardComponent } from './group-card';
import { GroupsService, Group } from '../../groups.service';
import { ConfigService } from '../../../../core/config.service';

const mockGroup: Group = {
  id: 'g-1',
  name: 'Test Group',
  created_by: 'u-1',
  created_at: '2026-01-01T00:00:00Z',
  member_count: 2,
};

describe('GroupCardComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [GroupCardComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: GroupsService,
          useValue: {
            renameGroup: () => of(mockGroup),
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
    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows group name', () => {
    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Test Group');
  });

  it('shows member count', () => {
    const fixture = TestBed.createComponent(GroupCardComponent);
    fixture.componentRef.setInput('group', mockGroup);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('2 miembros');
  });
});
