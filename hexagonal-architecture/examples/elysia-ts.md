# Hexagonal Architecture with ElysiaJS

A self-contained example of **Hexagonal Architecture** (Ports & Adapters) using TypeScript and [ElysiaJS](https://elysiajs.com)—a type-safe, Bun-first web framework. It follows the patterns in the main [SKILL.md](../SKILL.md): ports in the owning domain, dependency rule, and simple DTOs at boundaries.

## Concepts used

- **Dependency Rule**: Dependencies point **inward only**. Domain has no framework or DB imports; application depends on domain; infrastructure (routes, repositories) depends on application/domain.
- **Port**: Interface that defines what a domain exposes or needs (e.g. `IFeedServicePort`). Lives in the **owning domain** (`feed/ports/`). The domain depends on the port, not on concrete implementations.
- **Adapter**: Class that implements a port. **Primary** adapters drive the app (HTTP routes); **secondary** adapters are used by the app (repositories, external APIs).
- **Data at boundaries**: Only **simple DTOs** (e.g. `FeedData`) cross port boundaries—never ORM entities or DB rows. Aligns with Clean Architecture: *"data crossing boundaries in the form most convenient for the inner circle."*
- **Repository**: **Driven port** (Fowler: collection-like interface for domain objects). Application uses the repository abstraction; infrastructure implements it. Domain stays independent of persistence.
- **Thin primary adapters**: Route handlers parse input → call use case (service) → return response. No business logic in handlers.
- **Wiring**: Elysia plugins use `.decorate()` to inject shared instances and `.derive()` to build dependent ones. Other domains depend on a plugin via `.use(plugin)` and receive its decorated context (e.g. `feedPort`).

## Prerequisites

- [Bun](https://bun.sh) (or Node with Elysia supported).
- Install: `bun add elysia` (or `npm i elysia`).

## Project structure

```
src/
├── index.ts                    # App entry: compose plugins and listen
├── modules/
│   ├── common/
│   │   └── repositories/       # BaseRepository (infrastructure)
│   ├── feed/
│   │   ├── ports/              # IFeedServicePort (Feed domain boundary)
│   │   ├── adapters/           # FeedServiceAdapter (implements port)
│   │   ├── repositories/       # FeedRepository
│   │   ├── feed.model.ts       # TypeBox schemas
│   │   ├── feed.service.ts     # Application logic
│   │   └── index.ts            # feedPlugin (routes + wiring)
│   └── comment/
│       ├── comment.model.ts
│       ├── comment.service.ts
│       ├── repositories/
│       └── index.ts             # commentPlugin, .use(feedPlugin)
```

The `user` in handlers is assumed to be set by an auth plugin (e.g. JWT) via `.decorate('user', ...)` or a `beforeHandle` that resolves the user from the request.

---

## Pattern 1: Port Interface Definition

Ports define the contract between the domain and external systems. In TypeScript they are plain interfaces.

```typescript
// src/modules/feed/ports/IFeedService.port.ts

/**
 * Feed service port interface (Feed domain boundary)
 * Other domains access Feed domain features through this interface
 */
export interface IFeedServicePort {
  /**
   * Find feeds by author ID
   * @param authorId Author ID
   * @returns List of feeds
   */
  findByAuthorId(authorId: bigint): Promise<FeedData[]>;

  /**
   * Increment feed's comment count
   * @param feedId Feed ID
   */
  incrementCommentCount(feedId: bigint): Promise<void>;

  /**
   * Decrement feed's comment count
   * @param feedId Feed ID
   */
  decrementCommentCount(feedId: bigint): Promise<void>;
}

/** Data transfer object for the port */
export interface FeedData {
  id: bigint;
  content: string;
  likeCount: number;
  commentCount: number;
}
```

## Pattern 2: Adapter Implementation

Adapters implement port interfaces. In Elysia, we use plain classes and wire them via plugins (no framework-specific decorators).

```typescript
// src/modules/feed/adapters/feed.service.adapter.ts

import type { IFeedServicePort, FeedData } from '../ports/IFeedService.port';
import { FeedService } from '../feed.service';

/**
 * Feed service adapter
 * Implements IFeedServicePort interface to provide Feed features to other domains
 */
export class FeedServiceAdapter implements IFeedServicePort {
  constructor(private readonly feedService: FeedService) {}

  /**
   * Find feeds by author ID
   * @param authorId Author ID
   * @returns List of feeds (only ID, content, and counts)
   */
  async findByAuthorId(authorId: bigint): Promise<FeedData[]> {
    const feeds = await this.feedService.findByAuthorId(authorId);
    return feeds.map((feed) => ({
      id: feed.id,
      content: feed.content,
      likeCount: feed.likeCount,
      commentCount: feed.commentCount,
    }));
  }

  /**
   * Increment feed's comment count
   * @param feedId Feed ID
   */
  async incrementCommentCount(feedId: bigint): Promise<void> {
    await this.feedService.incrementCommentCount(feedId);
  }

  /**
   * Decrement feed's comment count
   * @param feedId Feed ID
   */
  async decrementCommentCount(feedId: bigint): Promise<void> {
    await this.feedService.decrementCommentCount(feedId);
  }
}
```

## Pattern 3: Module Configuration with Elysia Plugins

Elysia uses plugins and `.decorate()` to wire ports and adapters. Each domain is a plugin that exports its port for other plugins.

```typescript
// src/modules/feed/feed.plugin.ts
// Wire feed repository, service, and port; register routes and models.

import { Elysia } from 'elysia';
import { t } from 'elysia';
import { FeedService } from './feed.service';
import { FeedRepository } from './repositories/feed.repository';
import { FeedServiceAdapter } from './adapters/feed.service.adapter';
import type { IFeedServicePort } from './ports/IFeedService.port';
import { feedModels } from './feed.model';

export const feedPlugin = new Elysia({ name: 'feed' })
  .decorate('feedRepository', new FeedRepository(/* db client */))
  .derive(({ feedRepository }) => ({
    feedService: new FeedService(feedRepository),
  }))
  .derive(({ feedService }) => ({
    feedPort: new FeedServiceAdapter(feedService) as IFeedServicePort,
  }))
  .model(feedModels)
  .get('/feeds', ({ feedService, user }) => feedService.findByAuthorId(user.id), {
    response: { 200: t.Object({ feeds: t.Array(t.Any()), total: t.Number() }) },
    // auth guard applied via .use(authPlugin)
  })
  .post('/feeds', ({ body, feedService, user }) => feedService.create(body, user.id), {
    body: 'CreateFeed',
    response: { 201: t.Object({ id: t.String(), content: t.String() }) },
  });
```

Other plugins that need the Feed port call `.use(feedPlugin)` and then receive `feedPort` on the request context (Pattern 6).

## Pattern 4: Repository Pattern (Infrastructure Layer)

Repositories abstract data access and act as the **driven port** for persistence (Fowler: collection-like interface; domain stays unaware of storage). Plain classes; no Elysia-specific code in the repository. The application layer depends on the repository; the concrete implementation lives in infrastructure.

```typescript
// src/modules/common/repositories/base.repository.ts

/**
 * Base repository providing common CRUD operations
 * Wraps the data access layer for better testability and abstraction
 */
export abstract class BaseRepository<T> {
  constructor(
    protected readonly db: unknown,
    protected readonly modelName: string,
  ) {}

  /** Find entity by ID */
  async findById(id: bigint): Promise<T | null> {
    return (this.db as any)[this.modelName].findUnique({ where: { id } });
  }

  /** Find multiple entities */
  async findMany(args?: any): Promise<T[]> {
    return (this.db as any)[this.modelName].findMany(args);
  }

  /** Create new entity */
  async create(data: any): Promise<T> {
    return (this.db as any)[this.modelName].create({ data });
  }

  /** Update existing entity */
  async update(id: bigint, data: any): Promise<T> {
    return (this.db as any)[this.modelName].update({ where: { id }, data });
  }

  /** Delete entity */
  async delete(id: bigint): Promise<T> {
    return (this.db as any)[this.modelName].delete({ where: { id } });
  }
}
```

```typescript
// src/modules/feed/repositories/feed.repository.ts

import { BaseRepository } from '../../common/repositories/base.repository';

export interface FeedEntity {
  id: bigint;
  authorId: bigint;
  content: string;
  likeCount: number;
  commentCount: number;
  deletedAt: Date | null;
  createdAt: Date;
}

/**
 * Feed repository
 * Handles all database operations for Feed entities
 */
export class FeedRepository extends BaseRepository<FeedEntity> {
  constructor(db: unknown) {
    super(db, 'feed');
  }

  /**
   * Find feeds by author ID
   * @param authorId Author ID
   * @returns Feeds ordered by creation date (newest first), excluding soft-deleted
   */
  async findByAuthorId(authorId: bigint): Promise<FeedEntity[]> {
    return this.findMany({
      where: { authorId, deletedAt: null },
      orderBy: { createdAt: 'desc' },
    });
  }
}
```

## Pattern 5: Layered Architecture Example

Presentation = Elysia routes; Application = service classes; Infrastructure = repositories. **DTOs at boundaries**: request/response and port DTOs (e.g. `FeedData`) are simple data structures—no ORM or framework types cross inward. Use TypeBox in the model layer and reference models by name where possible.

```typescript
// === MODEL LAYER (schemas + types) ===
// src/modules/feed/feed.model.ts

import { t } from 'elysia';

/** TypeBox schema for create-feed request body */
export const CreateFeedBody = t.Object({
  content: t.String({ minLength: 1, maxLength: 5000 }),
});

export const feedModels = {
  CreateFeed: CreateFeedBody,
};

export type CreateFeedBody = typeof CreateFeedBody.static;
```

```typescript
// === APPLICATION LAYER ===
// src/modules/feed/feed.service.ts

import { status } from 'elysia';
import type { FeedRepository } from './repositories/feed.repository';

/**
 * Feed service
 * Contains business logic for feed management
 */
export class FeedService {
  constructor(private readonly feedRepository: FeedRepository) {}

  /**
   * Find feeds by author ID
   * Business logic: only non-deleted feeds, sorted by creation date
   * @param authorId Author ID
   * @returns List of feeds and total count
   */
  async findByAuthorId(authorId: bigint) {
    const feeds = await this.feedRepository.findByAuthorId(authorId);
    return {
      feeds: feeds.map((f) => ({
        id: f.id.toString(),
        content: f.content,
        likeCount: f.likeCount,
        commentCount: f.commentCount,
        createdAt: f.createdAt,
      })),
      total: feeds.length,
    };
  }

  /**
   * Create a new feed
   * @param body Request body with content
   * @param authorId Author ID
   * @returns Created feed id and content
   */
  async create(body: { content: string }, authorId: bigint) {
    const feed = await this.feedRepository.create({
      authorId,
      content: body.content,
      likeCount: 0,
      commentCount: 0,
    });
    return { id: feed.id.toString(), content: feed.content };
  }

  /**
   * Increment feed's comment count
   * @param feedId Feed ID
   */
  async incrementCommentCount(feedId: bigint): Promise<void> {
    const feed = await this.feedRepository.findById(feedId);
    if (!feed) return status(404, 'Feed not found') as any;
    await this.feedRepository.update(feedId, { commentCount: feed.commentCount + 1 });
  }

  /**
   * Decrement feed's comment count
   * @param feedId Feed ID
   */
  async decrementCommentCount(feedId: bigint): Promise<void> {
    const feed = await this.feedRepository.findById(feedId);
    if (!feed) return;
    if (feed.commentCount > 0) {
      await this.feedRepository.update(feedId, { commentCount: feed.commentCount - 1 });
    }
  }
}
```

```typescript
// === PRESENTATION LAYER (Elysia as controller) ===
// src/modules/feed/index.ts – route handlers only; delegates to FeedService and exposes feedPort for other plugins.

import { Elysia, t, status } from 'elysia';
import { FeedService } from './feed.service';
import { FeedRepository } from './repositories/feed.repository';
import { FeedServiceAdapter } from './adapters/feed.service.adapter';
import type { IFeedServicePort } from './ports/IFeedService.port';
import { feedModels } from './feed.model';

export const feedPlugin = new Elysia({ name: 'feed' })
  .model(feedModels)
  .decorate('feedRepository', new FeedRepository(/* inject db */))
  .derive(({ feedRepository }) => ({
    feedService: new FeedService(feedRepository),
  }))
  .derive(({ feedService }) => ({
    feedPort: new FeedServiceAdapter(feedService) as IFeedServicePort,
  }))
  .get('/feeds', ({ feedService, user }) => feedService.findByAuthorId(user.id), {
    response: { 200: t.Object({ feeds: t.Array(t.Any()), total: t.Number() }) },
  })
  .post('/feeds', ({ body, feedService, user }) => feedService.create(body, user.id), {
    body: 'CreateFeed',
    response: { 201: t.Object({ id: t.String(), content: t.String() }) },
  });
```

## Pattern 6: Using Port in Another Module

A second domain (Comment) needs to call Feed operations (e.g. increment comment count). It depends only on the **port**: it `.use(feedPlugin)` and uses the decorated `feedPort` in handlers. It does not import FeedService or Feed internals. The Comment module is structured like Feed (CommentRepository, CommentService, comment models); below only the integration with `feedPort` is shown.

```typescript
// src/modules/comment/index.ts
// Comment plugin: .use(feedPlugin) provides feedPort on context.

import { Elysia, t, status } from 'elysia';
import { feedPlugin } from '../feed';
import { CommentService } from './comment.service';
import { commentModels } from './comment.model';

export const commentPlugin = new Elysia({ name: 'comment' })
  .use(feedPlugin) // Declare dependency – provides feedPort on context
  .model(commentModels)
  .decorate('commentRepository', new CommentRepository(/* db */))
  .derive(({ commentRepository }) => ({
    commentService: new CommentService(commentRepository),
  }))
  .get('/feeds/:feedId/comments', async ({ params, feedPort, commentService, user }) => {
    const feeds = await feedPort.findByAuthorId(user.id);
    const exists = feeds.some((f) => f.id.toString() === params.feedId);
    if (!exists) return status(404, 'Feed not found');
    const comments = await commentService.findByFeedId(BigInt(params.feedId));
    return { comments };
  }, {
    params: t.Object({ feedId: t.String() }),
    response: { 200: t.Object({ comments: t.Array(t.Any()) }), 404: t.String() },
  })
  .post('/comments', async ({ body, feedPort, commentService, user }) => {
    const comment = await commentService.create(body, user.id);
    await feedPort.incrementCommentCount(body.feedId);
    return { comment };
  }, {
    body: 'CreateComment',
    response: { 201: t.Object({ comment: t.Any() }) },
  })
  .delete('/comments/:id', async ({ params, feedPort, commentService, user }) => {
    const comment = await commentService.findById(BigInt(params.id));
    await commentService.delete(BigInt(params.id), user.id);
    await feedPort.decrementCommentCount(comment.feedId);
    return { success: true };
  }, {
    params: t.Object({ id: t.String() }),
    response: { 200: t.Object({ success: t.Literal(true) }) },
  });
```

## Main App Wiring

Compose plugins at the root. Order matters: any auth or shared decorators (e.g. `user`) must be applied before feature plugins that use them.

```typescript
// src/index.ts

import { Elysia } from 'elysia';
import { feedPlugin } from './modules/feed';
import { commentPlugin } from './modules/comment';
// import { authPlugin } from './plugins/auth';

const app = new Elysia()
  // .use(authPlugin)
  .use(feedPlugin)
  .use(commentPlugin)
  .listen(3000);
```

## Benefits Demonstrated

1. **Dependency Inversion**: Comment plugin depends on `feedPort` (abstraction), not `FeedService` or Feed plugin internals.
2. **Testability**: In tests, mount a minimal Elysia with a mock `feedPort` via `.decorate('feedPort', mockFeedPort)`.
3. **Flexibility**: Swap `FeedServiceAdapter` or the real repository for in-memory implementations without changing route handlers.
4. **Layer separation**: Routes = presentation; services = application; repositories = infrastructure; ports = domain boundaries.
5. **Elysia alignment**: One plugin per feature, explicit `.use(feedPlugin)` for dependencies, TypeBox models and reference-by-name for validation.

---

**See also:** [SKILL.md](../SKILL.md) (dependency rule, what crosses boundaries, CQRS/events, repository pattern), [references/LAYERS.md](../references/LAYERS.md), [references/HEXAGONAL.md](../references/HEXAGONAL.md), [references/CHEATSHEET.md](../references/CHEATSHEET.md).

**Further reading:** [Elysia docs](https://elysiajs.com), [Elysia for LLMs](https://elysiajs.com/llms.txt) (routes, plugins, validation).
