# v-dotnet-as-java

Explains .NET, C# and ASP.NET Core to a senior Java (Spring Boot) developer through precise analogies to the Java ecosystem, and warns where those analogies break. Unlike the other skills in this marketplace, it fires automatically: Claude uses it whenever a question or task involves .NET.

## What it is

A set of instructions that changes how Claude answers .NET questions and how it writes or reviews C#. For a concept, the answer follows four steps:

1. **What it is in .NET**, the way a .NET developer thinks about it.
2. **The Java equivalent**, from a fixed mapping table: ASP.NET Core ↔ Spring Boot, EF Core ↔ JPA/Hibernate, NuGet ↔ Maven Central, `.csproj` ↔ `pom.xml`, xUnit ↔ JUnit 5, Moq ↔ Mockito, LINQ ↔ Stream API, `IOptions<T>` ↔ `@ConfigurationProperties`, and about twenty more.
3. **Where the analogy breaks**: the part that matters most, never skipped when a trap exists.
4. Side-by-side snippets when useful, Java first, then C#.

Quick factual questions get a short answer instead of the full template.

It always warns about the **false friends**, where Java intuition causes real bugs: `async/await` is not Loom or `CompletableFuture` (`.Result` can deadlock), `IQueryable` translates to SQL (an early `.ToList()` loads the whole table), EF Core change tracking differs from Hibernate, `string?` is not `Optional`, there are no checked exceptions, injecting a Scoped service into a Singleton fails at startup, and `internal` replaces package-private.

It also tells legacy **.NET Framework 4.x** (`net48`, `Web.config`, IIS, `System.Web`) apart from modern .NET, compares the move between them to Java EE → Spring Boot, and says which world an answer applies to.

When writing or reviewing C#, it uses idiomatic modern C# and briefly explains idioms you may not know yet, and points out where a Java habit produced non-idiomatic code (getter methods instead of properties, hand-written `equals`/`hashCode` instead of records, `.Result` on tasks).

## What problem it solves

An experienced Java developer can read C# on day one, which is exactly the risk: it looks familiar enough that Java habits carry over silently. Most of them are harmless, but a few cause production incidents (blocking on async code, materialising a query too early, DI lifetime mistakes). Generic .NET documentation explains the concepts from scratch and does not say which of your instincts to distrust.

This skill anchors every explanation to what you already know (Spring, Maven, JPA, JUnit), so learning is faster, and makes the traps explicit instead of letting Claude quietly write correct C# you do not understand.

## When to use it

It triggers by itself on questions or code involving C#, .NET, ASP.NET Core, Entity Framework, NuGet, MSBuild or xUnit, and on reviewing or writing C# on a .NET project, even without a request for a Java comparison. You can also call it directly with `/v-dotnet-as-java`.

It is most useful when:

- joining or onboarding onto a .NET codebase
- reviewing C# you or Claude wrote, to catch Java-shaped code
- deciding between .NET libraries or patterns and wanting the Spring equivalent as a reference point
- working in a legacy .NET Framework project and needing to know what differs from modern .NET

The analogies are anchored to Java and Spring, not Kotlin, because your Kotlin knowledge is shallow.

## Maintainer notes

The skill is a living document. When an analogy misleads or a concept still confuses, add it to the mapping table or the "False friends" list in `SKILL.md`. It was copied from the unprefixed personal skill `~/.claude/skills/dotnet-for-java-devs`; the two copies are separate, so a change here does not reach the personal one.
