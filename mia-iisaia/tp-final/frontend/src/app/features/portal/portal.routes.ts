import { Routes } from '@angular/router';

export const portalRoutes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/portal-page/portal-page').then((m) => m.PortalPage),
  },
];
