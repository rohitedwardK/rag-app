import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Document {
  filename: string;
  uploaded_at: string;
}

export interface UploadResponse {
  filename: string;
  chunks_created: number;
  text_length: number;
}

export interface ChatResponse {
  response: string;
  sources: string[];
}

export interface HealthResponse {
  status: string;
  ollama_url: string;
  llm_model: string;
  embed_model: string;
}

export interface ModelStatusResponse {
  llm_model: string;
  embed_model: string;
  llm_active: boolean;
  embed_active: boolean;
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`);
  }

  getModelStatus(): Observable<ModelStatusResponse> {
    return this.http.get<ModelStatusResponse>(`${this.baseUrl}/model-status`);
  }

  uploadDocument(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.baseUrl}/upload`, formData);
  }

  getDocuments(): Observable<Document[]> {
    return this.http.get<Document[]>(`${this.baseUrl}/documents`);
  }

  deleteDocument(filename: string): Observable<{ status: string; filename: string }> {
    return this.http.delete<{ status: string; filename: string }>(
      `${this.baseUrl}/documents/${encodeURIComponent(filename)}`
    );
  }

  chat(message: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.baseUrl}/chat`, { message });
  }
}
