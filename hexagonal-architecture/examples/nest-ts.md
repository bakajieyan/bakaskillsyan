# Hexagonal Architecture with NestJS

A self-contained example of **Hexagonal Architecture** (Ports & Adapters) using TypeScript and [NestJS](https://nestjs.com)—a progressive Node.js framework with dependency injection and modular structure. It follows the patterns in the main [SKILL.md](../SKILL.md): ports in the owning domain, dependency rule, and simple DTOs at boundaries.

## Concepts used

- **Dependency Rule**: Dependencies point **inward only**. Domain has no framework or DB imports; application depends on domain; infrastructure (controllers, repositories) depends on application/domain.
- **Port**: Interface that defines what a domain exposes or needs (e.g. `IFeedServicePort`). Lives in the **owning domain** (`feed/ports/`). The domain depends on the port, not on concrete implementations.
- **Adapter**: Class that implements a port. **Primary** adapters drive the app (controllers); **secondary** adapters are used by the app (repositories, external APIs).
- **Data at boundaries**: Only **simple DTOs** (e.g. `FeedData`) cross port boundaries—never ORM entities or DB rows. Aligns with Clean Architecture: *"data crossing boundaries in the form most convenient for the inner circle."*
- **Repository**: **Driven port** (Fowler: collection-like interface for domain objects). Application uses the repository abstraction; infrastructure implements it. Domain stays independent of persistence.
- **Thin primary adapters**: Controllers parse input → call use case (service) → serialize response. No business logic in controllers.
- **Wiring**: NestJS modules use `providers` and `exports` to register implementations and expose ports. Other modules `import` the feature module and inject the port via `@Inject('IFeedServicePort')`.

## Prerequisites

- [Node.js](https://nodejs.org) 18+
- NestJS: `npm i @nestjs/common @nestjs/core @nestjs/platform-express reflect-metadata rxjs` (or use `nest new`).
- Optional: Prisma (or any ORM) for the repository examples; the patterns work with any data layer.

## Project structure

```
src/
├── main.ts                         # Bootstrap Nest application
├── app.module.ts                   # Root module: imports feature modules
├── modules/
│   ├── common/
│   │   ├── repositories/           # BaseRepository (infrastructure)
│   │   └── decorators/             # @GetUser(), auth guards (optional)
│   ├── feed/
│   │   ├── ports/                  # IFeedServicePort (Feed domain boundary)
│   │   ├── adapters/               # FeedServiceAdapter (implements port)
│   │   ├── repositories/           # FeedRepository
│   │   ├── dto/                    # Request/response DTOs
│   │   ├── feed.controller.ts
│   │   ├── feed.service.ts
│   │   └── feed.module.ts
│   └── comment/
│       ├── comment.controller.ts   # Injects IFeedServicePort
│       ├── comment.service.ts
│       └── comment.module.ts       # Imports FeedModule
```

The `user` in controllers is assumed to be set by an auth guard (e.g. JWT) and a `@GetUser()` decorator that reads the authenticated user from the request.

---

## Pattern 1: Port Interface Definition

Ports define the contract between the domain and external systems. In TypeScript, we use interfaces to declare these contracts.

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

Adapters implement the port interfaces and connect the domain to the infrastructure.

```typescript
// src/modules/feed/adapters/feed.service.adapter.ts

import { Injectable } from '@nestjs/common';
import { IFeedServicePort, FeedData } from '../ports/IFeedService.port';
import { FeedService } from '../feed.service';

/**
 * Feed service adapter
 * Implements IFeedServicePort interface to provide Feed features to other domains
 */
@Injectable()
export class FeedServiceAdapter implements IFeedServicePort {
  constructor(private readonly feedService: FeedService) {}

  /**
   * Find feeds by author ID
   * @param authorId Author ID
   * @returns List of feeds (only ID, content, and counts)
   */
  async findByAuthorId(authorId: bigint): Promise<FeedData[]> {
    const feeds = await this.feedService.findByAuthorId(authorId);

    // Map domain entities to port DTOs
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

## Pattern 3: Module Configuration with Dependency Injection

NestJS modules wire together ports and adapters using dependency injection. The feature module registers the adapter as the port and exports the port token for other modules.

```typescript
// src/modules/feed/feed.module.ts

import { Module } from '@nestjs/common';
import { FeedController } from './feed.controller';
import { FeedService } from './feed.service';
import { FeedRepository } from './repositories/feed.repository';
import { FeedServiceAdapter } from './adapters/feed.service.adapter';

@Module({
  controllers: [FeedController],
  providers: [
    FeedService,
    FeedRepository,
    FeedServiceAdapter,
    {
      provide: 'IFeedServicePort', // Register port with DI container
      useClass: FeedServiceAdapter,
    },
  ],
  exports: ['IFeedServicePort'], // Export port for other modules (e.g. CommentModule)
})
export class FeedModule {}
```

Other modules that need the Feed port import `FeedModule` and inject `@Inject('IFeedServicePort')` in their controllers or services (Pattern 6).

## Pattern 4: Repository Pattern (Infrastructure Layer)

Repositories abstract data access and act as the **driven port** for persistence (Fowler: collection-like interface; domain stays unaware of storage). The example below uses a Prisma-like API; you can replace it with TypeORM, MikroORM, or a plain data client. The application layer depends on the repository type/interface; the concrete implementation lives in infrastructure.

```typescript
// src/modules/common/repositories/base.repository.ts

/**
 * Base repository providing common CRUD operations.
 * Assumes a Prisma-style client (prisma[modelName]); adapt for your ORM.
 */
export abstract class BaseRepository<T> {
  constructor(
    protected readonly prisma: { [key: string]: any },
    protected readonly modelName: string,
  ) {}

  protected getModel() {
    return this.prisma[this.modelName];
  }

  async findById(id: bigint): Promise<T | null> {
    return this.getModel().findUnique({ where: { id } });
  }

  async findMany(args?: any): Promise<T[]> {
    return this.getModel().findMany(args);
  }

  async create(data: any): Promise<T> {
    return this.getModel().create({ data });
  }

  async update(id: bigint, data: any): Promise<T> {
    return this.getModel().update({ where: { id }, data });
  }

  async delete(id: bigint): Promise<T> {
    return this.getModel().delete({ where: { id } });
  }
}
```

```typescript
// src/modules/feed/repositories/feed.repository.ts

import { Injectable } from '@nestjs/common';
import { BaseRepository } from '../../common/repositories/base.repository';

/** Feed entity shape (matches your persistence model; e.g. Prisma Feed) */
export interface FeedEntity {
  id: bigint;
  authorId: bigint;
  content: string;
  likeCount: number;
  commentCount: number;
  viewCount?: number;
  deletedAt: Date | null;
  createdAt: Date;
}

/**
 * Feed repository
 * Handles all database operations for Feed entities
 */
@Injectable()
export class FeedRepository extends BaseRepository<FeedEntity> {
  constructor(prisma: { feed: any }) {
    super(prisma, 'feed');
  }

  async findByAuthorId(authorId: bigint): Promise<FeedEntity[]> {
    return this.findMany({
      where: { authorId, deletedAt: null },
      orderBy: { createdAt: 'desc' },
    });
  }
}
```

## Pattern 5: Layered Architecture Example

Presentation = controllers; Application = services; Infrastructure = repositories. **DTOs at boundaries**: request/response and port DTOs (e.g. `FeedData`) are simple data structures—no ORM or framework types cross inward. This keeps the Dependency Rule intact.

```typescript
// === DTO (response shape) ===
// src/modules/feed/dto/feed-list-response.dto.ts

export interface FeedListResponseDto {
  feeds: Array<{
    id: string;
    content: string;
    likeCount: number;
    commentCount: number;
    viewCount?: number;
    createdAt: Date;
  }>;
  total: number;
}
```

```typescript
// === PRESENTATION LAYER ===
// src/modules/feed/feed.controller.ts

import { Controller, Get } from '@nestjs/common';
import { GetUser } from '../common/decorators/user.decorator';
import { FeedService } from './feed.service';
import { FeedListResponseDto } from './dto/feed-list-response.dto';

/** Authenticated user (set by auth guard + @GetUser() decorator) */
interface RequestUser {
  id: bigint;
}

@Controller('feeds')
// @UseGuards(AuthGuard) — apply your JWT/auth guard
export class FeedController {
  constructor(private readonly feedService: FeedService) {}

  @Get()
  async findAll(
    @GetUser() user: RequestUser,
  ): Promise<FeedListResponseDto> {
    return this.feedService.findByAuthorId(user.id);
  }
}
```

```typescript
// === APPLICATION LAYER ===
// src/modules/feed/feed.service.ts

import { Injectable, NotFoundException } from '@nestjs/common';
import { FeedRepository } from './repositories/feed.repository';
import { FeedListResponseDto } from './dto/feed-list-response.dto';

/**
 * Feed service
 * Contains business logic for feed management
 */
@Injectable()
export class FeedService {
  constructor(private readonly feedRepository: FeedRepository) {}

  /**
   * Find feeds by author ID
   * Business logic: Only return non-deleted feeds, sorted by creation date
   */
  async findByAuthorId(authorId: bigint): Promise<FeedListResponseDto> {
    const feeds = await this.feedRepository.findByAuthorId(authorId);

    return {
      feeds: feeds.map(feed => ({
        id: feed.id.toString(), // Convert BigInt to string for API
        content: feed.content,
        likeCount: feed.likeCount,
        commentCount: feed.commentCount,
        viewCount: feed.viewCount,
        createdAt: feed.createdAt,
      })),
      total: feeds.length,
    };
  }

  /**
   * Increment feed's comment count
   */
  async incrementCommentCount(feedId: bigint): Promise<void> {
    const feed = await this.feedRepository.findById(feedId);
    if (!feed) throw new NotFoundException('Feed not found');
    await this.feedRepository.update(feedId, { commentCount: feed.commentCount + 1 });
  }

  /**
   * Decrement feed's comment count
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

Infrastructure (repositories) is shown in Pattern 4.

## Pattern 6: Using Port in Another Module

The Comment module needs to call Feed operations (e.g. increment comment count). It depends only on the **port**: it imports `FeedModule` and injects `IFeedServicePort`. It does not import `FeedService` or Feed internals.

```typescript
// src/modules/comment/comment.controller.ts

import { Controller, Get, Post, Delete, Body, Param, Inject, NotFoundException } from '@nestjs/common';
import { GetUser } from '../common/decorators/user.decorator';
import { IFeedServicePort } from '../feed/ports/IFeedService.port';
import { CommentService } from './comment.service';
import { CreateCommentDto } from './dto/create-comment.dto';

interface RequestUser {
  id: bigint;
}

@Controller('comments')
// @UseGuards(AuthGuard)
export class CommentController {
  constructor(
    @Inject('IFeedServicePort')
    private readonly feedPort: IFeedServicePort,
    private readonly commentService: CommentService,
  ) {}

  @Get('feed/:feedId')
  async getCommentsForFeed(
    @Param('feedId') feedId: string,
    @GetUser() user: RequestUser,
  ) {
    const feeds = await this.feedPort.findByAuthorId(user.id);
    const feedExists = feeds.some((f) => f.id.toString() === feedId);
    if (!feedExists) throw new NotFoundException('Feed not found');
    const comments = await this.commentService.findByFeedId(BigInt(feedId));
    return { comments };
  }

  @Post()
  async createComment(@Body() dto: CreateCommentDto, @GetUser() user: RequestUser) {
    const comment = await this.commentService.create(dto, user.id);
    await this.feedPort.incrementCommentCount(dto.feedId);
    return { comment };
  }

  @Delete(':id')
  async deleteComment(@Param('id') id: string, @GetUser() user: RequestUser) {
    const comment = await this.commentService.findById(BigInt(id));
    await this.commentService.delete(BigInt(id), user.id);
    await this.feedPort.decrementCommentCount(comment.feedId);
    return { success: true };
  }
}
```

`CommentModule` imports `FeedModule` so the port is available:

```typescript
// src/modules/comment/comment.module.ts

import { Module } from '@nestjs/common';
import { CommentController } from './comment.controller';
import { CommentService } from './comment.service';
import { FeedModule } from '../feed/feed.module';

@Module({
  imports: [FeedModule],
  controllers: [CommentController],
  providers: [CommentService],
})
export class CommentModule {}
```

## Main App Wiring

Compose feature modules at the root. Order does not matter for Feed and Comment; ensure any global auth or config modules are loaded as needed.

```typescript
// src/app.module.ts

import { Module } from '@nestjs/common';
import { FeedModule } from './modules/feed/feed.module';
import { CommentModule } from './modules/comment/comment.module';

@Module({
  imports: [FeedModule, CommentModule],
})
export class AppModule {}
```

## Benefits Demonstrated

1. **Dependency Inversion**: CommentController depends on `IFeedServicePort` (abstraction), not FeedService or Feed module internals.
2. **Testability**: In tests, provide a mock `IFeedServicePort` via `{ provide: 'IFeedServicePort', useValue: mockFeedPort }`.
3. **Flexibility**: Swap `FeedServiceAdapter` or the repository for in-memory implementations without changing controllers.
4. **Layer separation**: Controllers = presentation; services = application; repositories = infrastructure; ports = domain boundaries.
5. **NestJS alignment**: One module per feature, explicit `imports`/`exports` for dependencies, token-based injection for ports.

---

**See also:** [SKILL.md](../SKILL.md) (dependency rule, what crosses boundaries, CQRS/events, repository pattern), [references/LAYERS.md](../references/LAYERS.md), [references/HEXAGONAL.md](../references/HEXAGONAL.md), [references/CHEATSHEET.md](../references/CHEATSHEET.md).

**Further reading:** [NestJS docs](https://docs.nestjs.com), [NestJS custom providers](https://docs.nestjs.com/fundamentals/custom-providers).