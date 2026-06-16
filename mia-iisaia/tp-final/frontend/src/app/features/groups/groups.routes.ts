import { Routes } from '@angular/router';

export const groupsRoutes: Routes = [
  {
    path: '',
    title: 'Mis Grupos',
    loadComponent: () => import('./pages/groups-page/groups-page').then((m) => m.GroupsPage),
  },
  {
    path: ':id',
    title: 'Detalle del Grupo',
    loadComponent: () =>
      import('./pages/group-detail-page/group-detail-page').then((m) => m.GroupDetailPage),
  },
];
