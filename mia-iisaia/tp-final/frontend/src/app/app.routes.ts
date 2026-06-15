import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadChildren: () => import('./features/portal/portal.routes').then((m) => m.portalRoutes),
  },
];
