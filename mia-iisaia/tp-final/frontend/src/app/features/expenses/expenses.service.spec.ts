import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';

import { ExpensesService } from './expenses.service';
import { ConfigService } from '../../core/config.service';

describe('ExpensesService', () => {
  let service: ExpensesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
      ],
    });
    service = TestBed.inject(ExpensesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('lists expenses for a group', () => {
    service.listExpenses('g-1').subscribe();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/groups/g-1/expenses');
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('creates an expense for a group', () => {
    const body = { description: 'Cena', amount: '45.00', date: '2026-06-10' };
    service.createExpense('g-1', body).subscribe();
    const req = httpMock.expectOne('http://localhost:8000/api/v1/groups/g-1/expenses');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    req.flush({ id: 'e-1', group_id: 'g-1', created_at: '2026-06-10T00:00:00Z', ...body });
  });
});
