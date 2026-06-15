import { TestBed } from '@angular/core/testing';
import { UserCardComponent } from './user-card';

describe('UserCardComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserCardComponent],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows a loading spinner when isLoading is true', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('isLoading', true);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('mat-spinner')).toBeTruthy();
  });

  it('shows error message when error is set', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('error', new Error('fail'));
    fixture.detectChanges();
    const alert = (fixture.nativeElement as HTMLElement).querySelector('[role="alert"]');
    expect(alert?.textContent).toContain('Could not load the authenticated user.');
  });

  it('shows user data when loaded', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('user', { id: 1, email: 'alice@example.com' });
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('pre')?.textContent).toContain(
      'alice@example.com',
    );
  });
});
