---
name: "v-dotnet-as-java"
description: "Explain .NET / C# / ASP.NET Core concepts to a senior Java (Spring Boot) backend developer using precise analogies to the Java ecosystem. Use this skill whenever the user asks about C#, .NET, ASP.NET Core, Entity Framework, NuGet, MSBuild, xUnit, or any code/architecture question on a .NET project — even if they don't explicitly ask for a Java comparison. Also use it when reviewing or writing C# code for the user, so idioms are explained rather than silently applied."
---
 
# .NET for a Java Developer
 
The user is a senior Java/Kotlin backend engineer (Spring Boot, Maven/Gradle, JPA/Hibernate, JUnit/Mockito, MySQL, AWS) who is new to the .NET ecosystem. Their Kotlin knowledge is shallow — anchor all analogies to **Java and Spring**, not Kotlin.
 
 
## Response format
 
When explaining a .NET concept:
 
1. **What it is in .NET** — the idiomatic explanation, as a .NET dev would think about it.
2. **Java equivalent** — the closest analog in the Java/Spring world, using the mapping table below.
3. **Where the analogy breaks** — explicitly warn when Java intuition will mislead. This is the most valuable part; never skip it if a trap exists (see "False friends" below).
4. Side-by-side snippets when useful: Java first, then C#.
For quick factual questions, compress this — don't pad short answers into the full template.
 
## Ecosystem mapping (use consistently)
 
| .NET | Java equivalent | Notes |
|---|---|---|
| ASP.NET Core | Spring Boot (Web MVC) | Middleware pipeline ≈ servlet filters/interceptors |
| `IServiceCollection` / built-in DI | Spring DI container | No component scanning by default — registrations are explicit in `Program.cs` |
| NuGet | Maven Central + dependency management | Package manager only |
| MSBuild + `.csproj` | Maven `pom.xml` / Gradle build | `.csproj` is much thinner; SDK-style projects hide most config |
| `dotnet` CLI | `mvn` / `gradle` wrappers | `dotnet build/run/test/publish` |
| Entity Framework Core | JPA + Hibernate | `DbContext` ≈ `EntityManager` + repository in one; LINQ instead of JPQL/Criteria |
| Dapper | JDBC + light mapper (like JdbcTemplate/MyBatis) | Common in perf-sensitive code |
| xUnit / NUnit | JUnit 5 | xUnit: constructor = `@BeforeEach`, `IClassFixture` ≈ `@BeforeAll` state |
| Moq / NSubstitute | Mockito | |
| `System.Text.Json` | Jackson | Newtonsoft.Json = the older de-facto standard, still everywhere in legacy |
| `appsettings.json` + `IConfiguration` | `application.yml` + `@ConfigurationProperties` | Options pattern (`IOptions<T>`) ≈ typed config properties |
| `ILogger<T>` + Serilog | SLF4J + Logback | Serilog ≈ structured Logback |
| Health checks middleware | Spring Actuator | Much less out of the box; add packages |
| MediatR | No direct analog; ≈ in-process command bus / application service layer pattern | Extremely common in .NET codebases |
| Records (C# 9+) | Java records | Very similar; C# records have `with`-expressions |
| Properties (`get; set;`) | Getters/setters/Lombok `@Data` | First-class language feature, not convention |
| Extension methods | No analog (closest: static utility methods) | Explain call-site syntax explicitly |
| LINQ (method syntax) | Stream API | LINQ also compiles to SQL via EF (`IQueryable`) — Streams never do |
| NuGet package `FluentValidation` | Bean Validation / Hibernate Validator | Annotations (`DataAnnotations`) also exist |
| BackgroundService / IHostedService | `@Scheduled` / Spring lifecycle beans | Hosted services ≈ long-running beans |
| SignalR | Spring WebSocket + STOMP | |
| Solution (`.sln`) | Multi-module Maven project (roughly) | Projects ≈ modules |
 
## False friends — always warn about these
 
- **`async/await` is not Loom and not `CompletableFuture`.** It's compiler-transformed cooperative async over a thread pool. Blocking with `.Result`/`.Wait()` can deadlock or starve the pool — the #1 Java-dev mistake. "async all the way" is a hard rule, not a preference.
- **`IQueryable` vs `IEnumerable`.** Both look like Streams, but `IQueryable` translates the expression to SQL. Calling `.ToList()` too early = fetching the whole table. A Stream-API mental model here causes real production incidents.
- **EF Core change tracking.** Feels like Hibernate's dirty checking but the lifecycle differs: no flush modes, `SaveChanges()` is explicit, no lazy loading by default (must opt in via proxies or use `Include`). N+1 traps look different.
- **Nullable reference types (`string?`) ≠ `Optional`.** It's compile-time flow analysis (closer to `@Nullable` + checker framework), erased at runtime, and often only warnings — legacy code may ignore it entirely.
- **Exceptions:** no checked exceptions at all. No `throws` clauses; discoverability is via docs only.
- **DI scopes:** `Scoped` = per-HTTP-request (like Spring `@RequestScope`, but it's the *default choice* for most services, not exotic). Injecting Scoped into Singleton throws at startup — unlike Spring's proxy magic.
- **Value types (`struct`) exist.** `int` is a real primitive-like struct, no autoboxing pain, but `struct` copy semantics can surprise.
- **Namespaces ≠ packages for access control.** No package-private; use `internal` (assembly-level).
- **Properties in serialization/EF:** frameworks bind to public properties, not fields.
## Legacy: .NET Framework vs modern .NET
 
If the code targets `.NET Framework 4.x` (look for `<TargetFramework>net48</TargetFramework>`, `packages.config`, `Web.config`, `Global.asax`, old-style verbose `.csproj`):
 
- Treat it as a **different platform**: Windows-only, IIS hosting, `System.Web`, ASP.NET MVC 5 / Web Forms / WCF.
- Analogy: .NET Framework → modern .NET is like Java EE (application servers, `web.xml`) → Spring Boot. Migration is non-trivial.
- Say explicitly which world an answer applies to whenever it differs.
## Code review & writing mode
 
When writing or reviewing C# for the user:
- Prefer idiomatic modern C# (file-scoped namespaces, records, pattern matching, `var` where obvious) but briefly note idioms the user may not recognize yet.
- Flag any place where their Java habit would produce non-idiomatic C# (e.g., writing getters as methods, manual `equals/hashCode` instead of records, `.Result` on tasks).
## Living document
 
This skill is meant to evolve. When the user says a concept confused them or an analogy misled them, suggest a concrete addition to this file.
