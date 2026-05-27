# LinkedIn Platform Architecture

This document describes the high-level design, software design patterns, and folder structure of the modularized LinkedIn professional networking system.

---

## 1. System Design Overview

The system is organized into a clean, layered architecture with modular separation of concerns. This structure conforms to modern clean code standards, separating entities (models), business logic (services), extensibility strategies, event observers, and platform core orchestration.

```
linkedin/
│
├── app/
│   ├── models/       # Pure domain objects and entity builders
│   ├── services/     # Pure business logic services (connections, newsfeeds, etc.)
│   ├── strategies/   # Extensible behavioral strategies (feed sorting)
│   ├── observers/    # Event-driven pub-sub classes (real-time notification delivery)
│   ├── core/         # Configuration, enums, and system orchestrators
│   └── demo/         # Sandbox scenario demonstrating end-to-end execution
│
└── docs/             # Diagrams and architectural guides
```

---

## 2. Design Patterns Implemented

The LinkedIn Platform leverages several foundational Design Patterns to enforce loose coupling, high cohesion, and single responsibility principles.

### A. Singleton Pattern
* **Location**: `app/core/linkedin_system.py`
* **Implementation**: Uses a thread-safe double-checked locking mechanism (`threading.Lock`) within the `__new__` method to guarantee that exactly one instance of the `LinkedInSystem` is created and shared across the application.
* **Purpose**: Coordinates access to the central in-memory database of registered members, connections, search indexes, and active services.

### B. Builder Pattern
* **Location**: `app/models/member.py`
* **Implementation**: The nested `Member.Builder` class provides a step-by-step fluid API to configure and construct complex `Member` objects:
  ```python
  alice = Member.Builder("Alice", "alice@example.com") \
      .with_summary("Senior Software Engineer...") \
      .add_experience(Experience(...)) \
      .add_education(Education(...)) \
      .build()
  ```
* **Purpose**: Decouples the representation and initialization process of a multi-faceted profile representation from the Member instance class itself.

### C. Observer Pattern
* **Location**: `app/observers/notification_observer.py`, `app/models/post.py`
* **Implementation**: The standard subject-observer structure allows a `Post` (inheriting from `Subject`) to notify registered `NotificationObserver` instances (e.g. the post `author`) when events like likes and comments occur.
* **Purpose**: Enables decoupled, real-time reactive notifications when interactive engagement is recorded on shared posts.

### D. Strategy Pattern
* **Location**: `app/strategies/feed_sorting_strategy.py`
* **Implementation**: Exposes an abstract base interface `FeedSortingStrategy` requiring a `sort(posts)` method, concretely implemented by `ChronologicalSortStrategy`.
* **Purpose**: Allows the system to dynamically plug in alternative ranking, relevance, or filtering algorithms for a member's news feed at runtime without modifying the news feed core.

---

## 3. High-Level Class Diagrams
UML Diagrams representing the class relationships and sequence workflows are located in the `docs` folder:
- **Class Diagram**: [docs/class_diagram.png](class_diagram.png)
- **Sequence Diagram**: [docs/sequence_diagram.png](sequence_diagram.png)
