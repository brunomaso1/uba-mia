import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink } from '@angular/router';
import { filter, map, startWith } from 'rxjs';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';

@Component({
  selector: 'app-header',
  imports: [
    RouterLink,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDividerModule,
  ],
  templateUrl: './app-header.html',
  styleUrl: './app-header.scss',
})
export class AppHeaderComponent {
  private readonly router = inject(Router);
  private readonly oidc = inject(OidcSecurityService);

  private getLeafTitle(): string {
    let route = this.router.routerState.snapshot.root;
    while (route.firstChild) route = route.firstChild;
    return route.title ?? '';
  }

  protected readonly pageTitle = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      startWith(null),
      map(() => this.getLeafTitle()),
    ),
    { initialValue: '' },
  );

  protected readonly username = computed(
    () => (this.oidc.userData().userData?.preferred_username as string) ?? '',
  );

  protected readonly email = computed(() => (this.oidc.userData().userData?.email as string) ?? '');

  protected readonly initial = computed(() => {
    const name = this.username();
    return name ? name[0].toUpperCase() : '?';
  });

  protected readonly navItems = [
    { label: 'Portal', path: '/' },
    { label: 'Grupos', path: '/groups' },
  ];

  protected logout(): void {
    this.oidc.logoff().subscribe();
  }
}
