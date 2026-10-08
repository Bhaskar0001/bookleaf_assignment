# REST API Specification

Base Path: `/api/v1`

## Authentication

### `POST /auth/login`
- **Request**:
  ```json
  {
    "email": "priya.sharma@bookleaf.com",
    "password": "Author@BookLeaf2026!"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "user": {
        "id": "c1f7b8...",
        "email": "priya.sharma@bookleaf.com",
        "role": "AUTHOR",
        "full_name": "Priya Sharma",
        "author_id": "AUTH001"
      }
    }
  }
  ```

### `GET /auth/me`
Returns the currently authenticated user session.

---

## Author Endpoints

### `GET /author/profile`
Returns author metrics: total books, published count, books in production, and cumulative royalty figures.

### `GET /author/books`
Returns author's books catalog.

### `GET /author/books/{book_id}`
Returns details for a book belonging to the author. Returns `403 FORBIDDEN` if another author's book is requested.

### `GET /author/tickets`
Returns support requests raised by the author.

### `POST /author/tickets`
Creates a support request with instant persistence and atomic `TICKET_CREATED` event.

### `GET /author/tickets/{ticket_id}`
Returns ticket view with conversation thread and ticket history. Internal notes are excluded.

### `POST /author/tickets/{ticket_id}/messages`
Sends a message from author. Rejected with `422` if ticket is `CLOSED`.

### `GET /author/timeline`
Consolidated operational timeline across all author requests.

---

## Admin Endpoints

### `GET /admin/tickets`
Queue of all tickets with filters: `status`, `category`, `priority`, `author_id`, `search`, and `sort_by`.

### `GET /admin/tickets/{ticket_id}`
Full single-screen workspace payload including internal notes.

### `GET /admin/tickets/{ticket_id}/relationships`
Returns duplicate candidate matches and confirmed links.

### `PATCH /admin/tickets/{ticket_id}/status`
Transitions ticket status according to state machine (`OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED`).

### `POST /admin/tickets/{ticket_id}/draft-response`
Generates an assistive draft response referencing BookLeaf policies.

### `POST /admin/tickets/{ticket_id}/link-duplicate`
Links duplicate ticket and emits `DUPLICATE_LINKED` events on both tickets.
