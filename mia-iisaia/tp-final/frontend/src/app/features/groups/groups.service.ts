import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ConfigService } from '../../core/config.service';

export interface Group {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
  member_count: number;
}

export interface Member {
  user_id: string;
  display_name: string;
  email: string;
  joined_at: string;
}

export interface UserPublic {
  id: string;
  display_name: string;
  email: string;
}

@Service()
export class GroupsService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(ConfigService);

  private get base(): string {
    return `${this.config.apiUrl()}/groups`;
  }

  createGroup(name: string): Observable<Group> {
    return this.http.post<Group>(this.base, { name });
  }

  renameGroup(id: string, name: string): Observable<Group> {
    return this.http.patch<Group>(`${this.base}/${id}`, { name });
  }

  deleteGroup(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${id}`);
  }

  addMember(groupId: string, userId: string): Observable<void> {
    return this.http.post<void>(`${this.base}/${groupId}/members`, {
      user_id: userId,
    });
  }
}
