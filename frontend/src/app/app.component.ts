import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService, Document, ChatResponse, HealthResponse, ModelStatusResponse } from './services/api.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="app">
      <header class="header">
        <h1>RAG Demo</h1>
        <p class="subtitle">Upload documents and chat with them using AI</p>
      </header>

      <main class="main">
        <!-- Status Banner -->
        <div class="status-banner" [class.connected]="isConnected" [class.error]="!isConnected && !checking">
          @if (checking) {
            <span>Checking connection...</span>
          } @else if (isConnected) {
            <div class="status-content">
              <span>Connected</span>
              <div class="model-badges">
                <span class="model-badge" [class.active]="modelStatus?.llm_active" [class.inactive]="modelStatus && !modelStatus.llm_active">
                  <span class="model-label">LLM:</span> {{ modelStatus?.llm_model || health?.llm_model }}
                </span>
                <span class="model-badge" [class.active]="modelStatus?.embed_active" [class.inactive]="modelStatus && !modelStatus.embed_active">
                  <span class="model-label">Embed:</span> {{ modelStatus?.embed_model || health?.embed_model }}
                </span>
              </div>
            </div>
          } @else {
            <span>Cannot connect to backend. Make sure the API is running on port 8000.</span>
          }
        </div>

        <div class="content">
          <!-- Left Panel: Documents -->
          <section class="panel documents-panel">
            <h2>Documents</h2>
            
            <div class="upload-area" 
                 (dragover)="onDragOver($event)" 
                 (dragleave)="onDragLeave($event)"
                 (drop)="onDrop($event)"
                 [class.dragover]="isDragging">
              <input type="file" 
                     #fileInput 
                     (change)="onFileSelected($event)" 
                     accept=".pdf,.txt,.md,.markdown,.docx,.html,.htm,.csv"
                     hidden>
              <div class="upload-content" (click)="fileInput.click()">
                <span class="upload-icon">📄</span>
                <span class="upload-text">Drop files here or click to upload</span>
                <span class="upload-hint">Supports PDF, TXT, MD, DOCX, HTML, CSV</span>
              </div>
            </div>

            @if (uploading) {
              <div class="upload-progress">
                <div class="spinner"></div>
                <span>Uploading and indexing...</span>
              </div>
            }

            @if (uploadError) {
              <div class="error-message">{{ uploadError }}</div>
            }

            <div class="documents-list">
              @if (documents.length === 0) {
                <p class="empty-state">No documents uploaded yet</p>
              } @else {
                @for (doc of documents; track doc.filename) {
                  <div class="document-item">
                    <div class="document-info">
                      <span class="document-name">{{ doc.filename }}</span>
                      <span class="document-date">{{ formatDate(doc.uploaded_at) }}</span>
                    </div>
                    <button class="btn-danger btn-sm" (click)="deleteDocument(doc.filename)" [disabled]="deleting">
                      Delete
                    </button>
                  </div>
                }
              }
            </div>
          </section>

          <!-- Right Panel: Chat -->
          <section class="panel chat-panel">
            <h2>Chat</h2>
            
            <div class="chat-messages" #chatContainer>
              @if (messages.length === 0) {
                <div class="empty-chat">
                  <span class="chat-icon">💬</span>
                  <p>Upload a document and start asking questions!</p>
                </div>
              } @else {
                @for (msg of messages; track $index) {
                  <div class="message" [class.user]="msg.role === 'user'" [class.assistant]="msg.role === 'assistant'">
                    <div class="message-content">{{ msg.content }}</div>
                    @if (msg.sources && msg.sources.length > 0) {
                      <div class="message-sources">
                        <span class="sources-label">Sources:</span>
                        @for (source of msg.sources; track source) {
                          <span class="source-tag">{{ source }}</span>
                        }
                      </div>
                    }
                  </div>
                }
              }
              @if (thinking) {
                <div class="message assistant">
                  <div class="message-content thinking">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              }
            </div>

            <div class="chat-input">
              <input type="text" 
                     [(ngModel)]="userMessage" 
                     (keyup.enter)="sendMessage()"
                     placeholder="Ask a question about your documents..."
                     [disabled]="thinking || documents.length === 0">
              <button class="btn-primary" 
                      (click)="sendMessage()" 
                      [disabled]="thinking || !userMessage.trim() || documents.length === 0">
                Send
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  `,
  styles: [`
    .app {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .header {
      background: linear-gradient(135deg, var(--primary), var(--primary-dark));
      color: white;
      padding: 1.5rem 2rem;
      text-align: center;

      h1 {
        font-size: 1.75rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
      }

      .subtitle {
        opacity: 0.9;
        font-size: 0.9375rem;
      }
    }

    .main {
      flex: 1;
      padding: 1.5rem;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }

    .status-banner {
      padding: 0.75rem 1rem;
      border-radius: var(--radius);
      margin-bottom: 1.5rem;
      font-size: 0.875rem;
      text-align: center;
      background: var(--bg);
      border: 1px solid var(--border);

      &.connected {
        background: #f0fdf4;
        border-color: var(--success);
        color: #166534;
      }

      &.error {
        background: #fef2f2;
        border-color: var(--error);
        color: #991b1b;
      }

      .status-content {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
      }

      .model-badges {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
      }

      .model-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.375rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8125rem;
        font-weight: 500;
        background: white;
        border: 2px solid var(--border);
        transition: all 0.2s ease;

        .model-label {
          color: var(--text-muted);
          font-weight: 400;
        }

        &.active {
          border-color: #22c55e;
          background: #f0fdf4;
          color: #166534;
          box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
        }

        &.inactive {
          border-color: #ef4444;
          background: #fef2f2;
          color: #991b1b;
          box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
        }
      }
    }

    .content {
      display: grid;
      grid-template-columns: 1fr 1.5fr;
      gap: 1.5rem;
      height: calc(100vh - 220px);

      @media (max-width: 900px) {
        grid-template-columns: 1fr;
        height: auto;
      }
    }

    .panel {
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 1.25rem;
      display: flex;
      flex-direction: column;

      h2 {
        font-size: 1.125rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--text);
      }
    }

    .upload-area {
      border: 2px dashed var(--border);
      border-radius: var(--radius);
      padding: 2rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.15s ease;

      &:hover, &.dragover {
        border-color: var(--primary);
        background: rgba(99, 102, 241, 0.05);
      }

      .upload-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
      }

      .upload-icon {
        font-size: 2rem;
      }

      .upload-text {
        font-weight: 500;
        color: var(--text);
      }

      .upload-hint {
        font-size: 0.8125rem;
        color: var(--text-muted);
      }
    }

    .upload-progress {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 1rem;
      color: var(--primary);
      font-size: 0.875rem;
    }

    .spinner {
      width: 20px;
      height: 20px;
      border: 2px solid var(--border);
      border-top-color: var(--primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .error-message {
      background: #fef2f2;
      color: var(--error);
      padding: 0.75rem;
      border-radius: var(--radius);
      margin-top: 0.75rem;
      font-size: 0.875rem;
    }

    .documents-list {
      margin-top: 1rem;
      flex: 1;
      overflow-y: auto;
    }

    .empty-state {
      color: var(--text-muted);
      text-align: center;
      padding: 2rem;
      font-size: 0.9375rem;
    }

    .document-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      margin-bottom: 0.5rem;

      .document-info {
        display: flex;
        flex-direction: column;
        gap: 0.125rem;
      }

      .document-name {
        font-weight: 500;
        font-size: 0.9375rem;
      }

      .document-date {
        font-size: 0.75rem;
        color: var(--text-muted);
      }
    }

    .btn-sm {
      padding: 0.375rem 0.75rem;
      font-size: 0.8125rem;
    }

    .chat-panel {
      display: flex;
      flex-direction: column;
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 0.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .empty-chat {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--text-muted);
      gap: 0.5rem;

      .chat-icon {
        font-size: 2.5rem;
      }
    }

    .message {
      max-width: 85%;

      &.user {
        align-self: flex-end;

        .message-content {
          background: var(--primary);
          color: white;
        }
      }

      &.assistant {
        align-self: flex-start;

        .message-content {
          background: var(--bg);
          color: var(--text);
        }
      }

      .message-content {
        padding: 0.75rem 1rem;
        border-radius: 1rem;
        font-size: 0.9375rem;
        line-height: 1.5;
        white-space: pre-wrap;

        &.thinking {
          display: flex;
          gap: 0.25rem;
          padding: 1rem 1.25rem;

          .dot {
            width: 8px;
            height: 8px;
            background: var(--text-muted);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;

            &:nth-child(1) { animation-delay: 0s; }
            &:nth-child(2) { animation-delay: 0.2s; }
            &:nth-child(3) { animation-delay: 0.4s; }
          }
        }
      }

      .message-sources {
        display: flex;
        flex-wrap: wrap;
        gap: 0.375rem;
        margin-top: 0.5rem;
        align-items: center;

        .sources-label {
          font-size: 0.75rem;
          color: var(--text-muted);
        }

        .source-tag {
          background: var(--bg);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
          color: var(--text-muted);
        }
      }
    }

    @keyframes bounce {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }

    .chat-input {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);

      input {
        flex: 1;
      }
    }
  `],
})
export class AppComponent implements OnInit {
  documents: Document[] = [];
  messages: ChatMessage[] = [];
  userMessage = '';
  
  uploading = false;
  uploadError = '';
  deleting = false;
  thinking = false;
  isDragging = false;
  
  isConnected = false;
  checking = true;
  health: HealthResponse | null = null;
  modelStatus: ModelStatusResponse | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.checkHealth();
    this.loadDocuments();
  }

  checkHealth(): void {
    this.checking = true;
    this.api.getHealth().subscribe({
      next: (health) => {
        this.health = health;
        this.isConnected = true;
        this.checking = false;
        this.checkModelStatus();
      },
      error: () => {
        this.isConnected = false;
        this.checking = false;
      },
    });
  }

  checkModelStatus(): void {
    this.api.getModelStatus().subscribe({
      next: (status) => {
        this.modelStatus = status;
      },
      error: () => {
        this.modelStatus = null;
      },
    });
  }

  loadDocuments(): void {
    this.api.getDocuments().subscribe({
      next: (docs) => (this.documents = docs),
      error: () => {},
    });
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging = false;
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.uploadFile(files[0]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.uploadFile(input.files[0]);
      input.value = '';
    }
  }

  uploadFile(file: File): void {
    this.uploading = true;
    this.uploadError = '';

    this.api.uploadDocument(file).subscribe({
      next: (result) => {
        this.uploading = false;
        this.loadDocuments();
      },
      error: (err) => {
        this.uploading = false;
        this.uploadError = err.error?.detail || 'Failed to upload document';
      },
    });
  }

  deleteDocument(filename: string): void {
    this.deleting = true;
    this.api.deleteDocument(filename).subscribe({
      next: () => {
        this.deleting = false;
        this.loadDocuments();
      },
      error: () => {
        this.deleting = false;
      },
    });
  }

  sendMessage(): void {
    if (!this.userMessage.trim() || this.thinking) return;

    const message = this.userMessage.trim();
    this.messages.push({ role: 'user', content: message });
    this.userMessage = '';
    this.thinking = true;

    this.api.chat(message).subscribe({
      next: (response) => {
        this.thinking = false;
        this.messages.push({
          role: 'assistant',
          content: response.response,
          sources: response.sources,
        });
      },
      error: (err) => {
        this.thinking = false;
        this.messages.push({
          role: 'assistant',
          content: 'Sorry, there was an error processing your request. Please try again.',
        });
      },
    });
  }

  formatDate(isoString: string): string {
    if (!isoString) return '';
    return new Date(isoString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
