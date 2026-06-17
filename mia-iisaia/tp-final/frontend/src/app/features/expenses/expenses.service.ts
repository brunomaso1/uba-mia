import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ConfigService } from '../../core/config.service';

export interface Expense {
  id: string;
  group_id: string;
  description: string | null;
  amount: string;
  date: string;
  created_at: string;
}

export interface ExpenseCreateBody {
  description: string | null;
  amount: string;
  date: string;
}

@Service()
export class ExpensesService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(ConfigService);

  private base(groupId: string): string {
    return `${this.config.apiUrl()}/groups/${groupId}/expenses`;
  }

  listExpenses(groupId: string): Observable<Expense[]> {
    return this.http.get<Expense[]>(this.base(groupId));
  }

  createExpense(groupId: string, body: ExpenseCreateBody): Observable<Expense> {
    return this.http.post<Expense>(this.base(groupId), body);
  }
}
