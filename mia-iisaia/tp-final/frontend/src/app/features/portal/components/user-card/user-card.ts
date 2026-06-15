import { Component, input } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-user-card',
  imports: [JsonPipe, MatCardModule, MatProgressSpinnerModule],
  templateUrl: './user-card.html',
  styleUrl: './user-card.scss',
})
export class UserCardComponent {
  readonly user = input<unknown>(undefined);
  readonly isLoading = input<boolean>(false);
  readonly error = input<Error | undefined>(undefined);
}
