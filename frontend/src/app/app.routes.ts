import { Routes } from '@angular/router';
import { RouteStub } from './route-stub';

export const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'home', component: RouteStub },
  { path: 'stem-portal', component: RouteStub },
  { path: 'student-portal', redirectTo: 'stem-portal', pathMatch: 'full' },
  { path: 'mentor-portal', component: RouteStub },
  { path: 'chatbot', component: RouteStub },
  { path: 'admin-portal', component: RouteStub },
  { path: '**', redirectTo: 'home' }
];
