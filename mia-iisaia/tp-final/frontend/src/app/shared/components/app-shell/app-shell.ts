import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AppHeaderComponent } from '../app-header/app-header';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, AppHeaderComponent],
  templateUrl: './app-shell.html',
})
export class AppShell {}
