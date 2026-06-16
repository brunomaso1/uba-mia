import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { of } from 'rxjs';

import { AddMemberFormComponent } from './add-member-form';
import { GroupsService } from '../../groups.service';
import { ConfigService } from '../../../../core/config.service';

describe('AddMemberFormComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddMemberFormComponent],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        {
          provide: GroupsService,
          useValue: { addMember: () => of(undefined) },
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
    const fixture = TestBed.createComponent(AddMemberFormComponent);
    fixture.componentRef.setInput('groupId', 'g-1');
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows all users as available when no members are loaded yet', () => {
    const fixture = TestBed.createComponent(AddMemberFormComponent);
    fixture.componentRef.setInput('groupId', 'g-1');
    fixture.componentRef.setInput('allUsers', [
      { id: 'u-1', display_name: 'Alice', email: 'alice@test.com' },
      { id: 'u-2', display_name: 'Bob', email: 'bob@test.com' },
    ]);
    fixture.detectChanges();

    // members.value() is undefined until the httpResource resolves → Set is empty → all pass filter
    const component = fixture.componentInstance as any;
    expect(component.availableUsers()).toHaveLength(2);
  });
});
