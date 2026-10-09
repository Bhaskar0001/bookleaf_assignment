export type Role = 'AUTHOR' | 'ADMIN';

export interface User {
  id: string;
  email: string;
  role: Role;
  fullName: string;
  authorId?: string;
}

export interface AuthorProfile {
  id: string;
  author_id: string;
  pen_name: string;
  phone?: string;
  email: string;
  total_books: number;
  published_books: number;
  books_in_production: number;
  total_royalties_earned: number | string;
  total_royalties_paid: number | string;
  total_royalties_pending: number | string;
  open_tickets: number;
}

export interface Book {
  id: string;
  book_id: string;
  author_id: string;
  title: string;
  isbn?: string | null;
  genre?: string | null;
  publication_date?: string | null;
  status: 'PUBLISHED' | 'IN_PRODUCTION' | 'DRAFT';
  mrp?: number | string | null;
  copies_sold: number;
  royalty_earned: number | string;
  royalty_paid: number | string;
  royalty_pending: number | string;
  print_partner?: string | null;
  available_on: string[];
  created_at: string;
}

export interface TicketBookSummary {
  id: string;
  book_id: string;
  title: string;
  isbn?: string | null;
  status?: string | null;
}

export interface TicketAuthorSummary {
  id: string;
  author_id: string;
  pen_name: string;
  email?: string;
}

export interface TicketMessage {
  id: string;
  sender_user_id: string;
  sender_name?: string;
  sender_role: 'AUTHOR' | 'ADMIN';
  message: string;
  created_at: string;
}

export interface TicketInternalNote {
  id: string;
  admin_user_id: string;
  admin_name?: string;
  note: string;
  created_at: string;
}

export interface TimelineEvent {
  id: string;
  ticket_id: string;
  ticket_number?: string;
  ticket_subject?: string;
  actor_user_id?: string;
  actor_name?: string;
  actor_role?: string;
  event_type: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface DuplicateSignals {
  same_author: boolean;
  same_book: boolean;
  subject_similarity: number;
  description_similarity: number;
  existing_status: string;
  recency_days: number;
}

export interface DuplicateCandidate {
  ticket_id?: string;
  ticketId?: string;
  ticket_number?: string;
  ticketNumber?: string;
  subject: string;
  status: string;
  similarity: number;
  reason: string;
  signals: DuplicateSignals;
}

export interface ConfirmedRelationship {
  id: string;
  source_ticket_id: string;
  source_ticket_number?: string;
  target_ticket_id: string;
  target_ticket_number?: string;
  relationship_type: string;
  detected_by: string;
  confirmed_by_name?: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  ticket_number: string;
  author_id: string;
  author?: TicketAuthorSummary;
  book_id?: string | null;
  book?: TicketBookSummary | null;
  subject: string;
  description: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
  category?: string | null;
  priority?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | null;
  system_category?: string | null;
  system_category_confidence?: number | null;
  category_source?: string | null;
  system_priority?: string | null;
  system_priority_confidence?: number | null;
  priority_source?: string | null;
  assigned_admin_id?: string | null;
  assigned_admin_name?: string | null;
  created_at: string;
  updated_at: string;
  resolved_at?: string | null;
  closed_at?: string | null;
  messages: TicketMessage[];
  internalNotes?: TicketInternalNote[];
}

export interface DraftResponse {
  draft_response: string;
  suggested_action?: string | null;
  requires_manual_verification: boolean;
  verification_notes?: string | null;
}
