# Hexagonal Architecture with Hono

A self-contained example of **Hexagonal Architecture** (Ports & Adapters) using TypeScript and [Hono](https://hono.dev)—a small, fast web framework built on Web Standards that runs on Cloudflare Workers, Deno, Bun, Node.js, and more. It follows the patterns in the main [SKILL.md](../SKILL.md): ports in the owning domain, dependency rule, and simple DTOs at boundaries.

## Concepts used

- **Dependency Rule**: Dependencies point **inward only**. Domain has no framework or DB imports; application depends on domain; infrastructure (handlers, repositories) depends on application/domain.
- **Port**: Interface that defines what a domain exposes or needs (e.g. `IFeedServicePort`). Lives in the **owning domain** (`feed/ports/`). The domain depends on the port, not on concrete implementations.
- **Adapter**: Class that implements a port. **Primary** adapters drive the app (HTTP routes); **secondary** adapters are used by the app (repositories, external APIs).
- **Data at boundaries**: Only **simple DTOs** (e.g. `FeedData`) cross port boundaries—never ORM entities or DB rows. Aligns with Clean Architecture: *"data crossing boundaries in the form most convenient for the inner circle."*
- **Repository**: **Driven port** (Fowler: collection-like interface for domain objects). Application uses the repository abstraction; infrastructure implements it. Domain stays independent of persistence.
- **Thin primary adapters**: Handlers parse input → call use case (service) → return `c.json()`. No business logic in handlers.
- **Wiring**: Hono uses middleware and typed **Variables** (`c.set()` / `c.get()`). Middleware creates repositories, services, and port adapters and attaches them to the request context so handlers depend on abstractions.

## Prerequisites

- Node 18+, Bun, or Deno.
- Install: `npm i hono` (or `bun add hono`). For validation: `npm i @hono/zod-validator zod`.

## Project structure

```
src/
├── index.ts                      # App entry: Hono app, middleware, routes, serve
├── modules/
│   ├── common/
│   │   └── repositories/        # BaseRepository (infrastructure)
│   ├── feed/
│   │   ├── ports/                # IFeedServicePort (Feed domain boundary)
│   │   ├── adapters/             # FeedServiceAdapter (implements port)
│   │   ├── repositories/         # FeedRepository
│   │   ├── feed.service.ts      # Application logic
│   │   ├── feed.routes.ts       # GET/POST /feeds handlers
│   │   └── feed.middleware.ts   # Sets feedRepository, feedService, feedPort
│   └── comment/
│       ├── comment.service.ts
│       ├── repositories/
│       ├── comment.routes.ts    # Comment handlers (use feedPort from context)
│       └── comment.middleware.ts
```

The `user` in handlers is assumed to be set by auth middleware (e.g. JWT) via `c.set('user', ...)` before route handlers run.

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

---

## Pattern 2: Adapter Implementation

Adapters implement port interfaces as plain classes. They are wired in middleware and attached to context.

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
    const result = await this.feedService.findByAuthorId(authorId);
    return result.feeds.map((f) => ({
      id: BigInt(f.id),
      content: f.content,
      likeCount: f.likeCount,
      commentCount: f.commentCount,
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

---

## Pattern 3: Module Configuration with Middleware and Variables

Hono has no built-in DI container. Use middleware to create instances and attach them to the request context with `c.set()`. Type the context with `Variables` so handlers get correct types via `c.get()`.

```typescript
// src/modules/feed/feed.middleware.ts

import { createMiddleware } from 'hono/factory';
import { FeedRepository } from './repositories/feed.repository';
import { FeedService } from './feed.service';
import { FeedServiceAdapter } from './adapters/feed.service.adapter';
import type { IFeedServicePort } from './ports/IFeedService.port';

/** Dependencies the feed domain adds to context */
export type FeedVariables = {
  feedRepository: FeedRepository;
  feedService: FeedService;
  feedPort: IFeedServicePort;
};

const feedRepository = new FeedRepository(/* db */);
const feedService = new FeedService(feedRepository);
const feedPort: IFeedServicePort = new FeedServiceAdapter(feedService);

/**
 * Middleware that attaches feed repository, service, and port to context.
 * Register before feed and comment routes so they can c.get('feedPort') etc.
 */
export const feedMiddleware = createMiddleware<{ Variables: FeedVariables }>(async (c, next) => {
  c.set('feedRepository', feedRepository);
  c.set('feedService', feedService);
  c.set('feedPort', feedPort);
  await next();
});
```

---

## Pattern 4: Repository Pattern (Infrastructure Layer)

Repositories abstract data access and act as the **driven port** for persistence (Fowler: collection-like interface; domain stays unaware of storage). Plain classes; no Hono-specific code. The application layer depends on the repository; the concrete implementation lives in infrastructure.

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

---

## Pattern 5: Layered Architecture Example

**Application layer**: service with business logic. **Presentation layer**: Hono handlers that call the service and return `c.json()` or error responses. **DTOs at boundaries**: port DTOs (e.g. `FeedData`) and response shapes are simple data structures—no ORM or framework types cross inward.

```typescript
// src/modules/feed/feed.service.ts

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
    if (!feed) return;
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
// src/modules/feed/feed.routes.ts – presentation layer

import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import type { FeedVariables } from './feed.middleware';

const createFeedSchema = z.object({
  content: z.string().min(1).max(5000),
});

type FeedEnv = { Variables: FeedVariables & { user: { id: bigint } } };

export const feedRoutes = new Hono<FeedEnv>()
  .get('/', (c) => {
    const feedService = c.get('feedService');
    const user = c.get('user'); // set by auth middleware
    return feedService.findByAuthorId(user.id).then((data) => c.json(data, 200));
  })
  .post(
    '/',
    zValidator('json', createFeedSchema),
    (c) => {
      const feedService = c.get('feedService');
      const user = c.get('user');
      const body = c.req.valid('json');
      return feedService.create(body, user.id).then((data) => c.json(data, 201));
    },
  );
```

---

## Pattern 6: Using Port in Another Module

The Comment domain needs to call Feed operations (e.g. increment comment count). It depends only on the **port**: it uses `c.get('feedPort')` in handlers. Comment middleware sets `commentService`; `feedPort` is already on context from feed middleware.

```typescript
// src/modules/comment/comment.middleware.ts

import { createMiddleware } from 'hono/factory';
import { CommentRepository } from './repositories/comment.repository';
import { CommentService } from './comment.service';
import type { FeedVariables } from '../feed/feed.middleware';

export type CommentVariables = {
  commentRepository: CommentRepository;
  commentService: CommentService;
};

const commentRepository = new CommentRepository(/* db */);
const commentService = new CommentService(commentRepository);

export const commentMiddleware = createMiddleware<{
  Variables: CommentVariables;
}>(async (c, next) => {
  c.set('commentRepository', commentRepository);
  c.set('commentService', commentService);
  await next();
});
```

```typescript
// src/modules/comment/comment.routes.ts

import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import type { FeedVariables } from '../feed/feed.middleware';
import type { CommentVariables } from './comment.middleware';

type CommentEnv = { Variables: FeedVariables & CommentVariables & { user: { id: bigint } } };

const createCommentSchema = z.object({
  feedId: z.string(),
  body: z.string(),
});

export const commentRoutes = new Hono<CommentEnv>()
  .get('/feeds/:feedId/comments', async (c) => {
    const feedPort = c.get('feedPort');
    const commentService = c.get('commentService');
    const user = c.get('user');
    const feedId = c.req.param('feedId');
    const feeds = await feedPort.findByAuthorId(user.id);
    const exists = feeds.some((f) => f.id.toString() === feedId);
    if (!exists) return c.json({ error: 'Feed not found' }, 404);
    const comments = await commentService.findByFeedId(BigInt(feedId));
    return c.json({ comments }, 200);
  })
  .post(
    '/comments',
    zValidator('json', createCommentSchema),
    async (c) => {
      const feedPort = c.get('feedPort');
      const commentService = c.get('commentService');
      const user = c.get('user');
      const body = c.req.valid('json');
      const comment = await commentService.create(body, user.id);
      await feedPort.incrementCommentCount(BigInt(body.feedId));
      return c.json({ comment }, 201);
    },
  )
  .delete('/comments/:id', async (c) => {
    const feedPort = c.get('feedPort');
    const commentService = c.get('commentService');
    const user = c.get('user');
    const id = c.req.param('id');
    const comment = await commentService.findById(BigInt(id));
    await commentService.delete(BigInt(id), user.id);
    await feedPort.decrementCommentCount(comment.feedId);
    return c.json({ success: true }, 200);
  });
```

---

## Main App Wiring

Compose middleware and routes. Order matters: feed middleware (which sets `feedPort`) must run before comment routes that use it. Use `app.route()` to mount route groups.

```typescript
// src/index.ts

import { Hono } from 'hono';
import { feedMiddleware } from './modules/feed/feed.middleware';
import { feedRoutes } from './modules/feed/feed.routes';
import { commentMiddleware } from './modules/comment/comment.middleware';
import { commentRoutes } from './modules/comment/comment.routes';

type AppVariables = import('./modules/feed/feed.middleware').FeedVariables &
  import('./modules/comment/comment.middleware').CommentVariables & {
    user: { id: bigint };
  };

const app = new Hono<{ Variables: AppVariables }>()
  .use('*', feedMiddleware)
  .use('*', commentMiddleware)
  // .use('*', authMiddleware)  // sets c.set('user', ...)
  .route('/feeds', feedRoutes)
  .route('/', commentRoutes); // e.g. GET /feeds/:feedId/comments, POST /comments, DELETE /comments/:id

export default app;
```

**Bun:**

```typescript
export default {
  port: 3000,
  fetch: app.fetch,
};
```

**Node.js** (with `@hono/node-server`):

```typescript
import { serve } from '@hono/node-server';
serve({ fetch: app.fetch, port: 3000 });
```

**Cloudflare Workers:** `export default app;`

---

## Benefits Demonstrated

1. **Dependency Inversion**: Comment handlers depend on `c.get('feedPort')` (abstraction), not FeedService or Feed internals.
2. **Testability**: In tests, call `app.request()` with a custom middleware that mocks `c.set('feedPort', mockFeedPort)` (or use a test Env).
3. **Flexibility**: Swap FeedServiceAdapter or the repository for in-memory implementations by changing what the middleware passes to `c.set()`.
4. **Layer separation**: Handlers = presentation; services = application; repositories = infrastructure; ports = domain boundaries.
5. **Hono alignment**: Web Standards, typed Variables, `app.route()` for structure, optional Zod (or other validators) for input validation.

---

**See also:** [SKILL.md](../SKILL.md) (dependency rule, what crosses boundaries, CQRS/events, repository pattern), [references/LAYERS.md](../references/LAYERS.md), [references/HEXAGONAL.md](../references/HEXAGONAL.md), [references/CHEATSHEET.md](../references/CHEATSHEET.md).

**Further reading:** [Hono documentation](https://hono.dev), [Hono for LLMs (full)](https://hono.dev/llms-full.txt) (routing, middleware, validation, RPC).
