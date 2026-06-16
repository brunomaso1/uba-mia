import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./shared/components/app-shell/app-shell').then((m) => m.AppShell),
    children: [
      {
        path: '',
        loadChildren: () => import('./features/portal/portal.routes').then((m) => m.portalRoutes),
      },
    ],
  },
];
