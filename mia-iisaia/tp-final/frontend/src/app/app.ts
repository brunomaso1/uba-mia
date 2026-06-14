import { Component, inject } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { RouterOutlet } from '@angular/router';
import { ConfigService } from './core/config.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, JsonPipe],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly config = inject(ConfigService);

  protected readonly apiUrl = this.config.apiUrl;
  protected readonly testInfo = httpResource(() => `${this.config.apiUrl()}/test`);
}
