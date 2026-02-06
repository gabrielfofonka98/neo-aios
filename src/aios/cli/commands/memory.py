"""Memory management commands for NEO-AIOS CLI."""

import click
from rich.console import Console
from rich.table import Table

from aios.context.memory import MemoryStore
from aios.context.memory_models import MemoryPriority
from aios.context.memory_models import MemoryType

console = Console()


@click.group(name="memory")
def memory_group() -> None:
    """Persistent memory management."""


@memory_group.command(name="list")
@click.option(
    "--type",
    "memory_type",
    type=click.Choice([t.value for t in MemoryType]),
    help="Filter by type.",
)
def memory_list(memory_type: str | None) -> None:
    """List all stored memories."""
    store = MemoryStore()
    memories = store.list_all()

    if memory_type:
        memories = [m for m in memories if m.memory_type.value == memory_type]

    if not memories:
        console.print("[dim]No memories found.[/dim]")
        return

    table = Table(title=f"Memories ({len(memories)})")
    table.add_column("ID", width=10)
    table.add_column("Type", width=10)
    table.add_column("Priority", width=10)
    table.add_column("Content", max_width=50)
    table.add_column("Tags")

    for m in memories[:50]:
        content = m.content[:47] + "..." if len(m.content) > 50 else m.content
        tags = ", ".join(m.tags) if m.tags else "-"
        table.add_row(m.id, m.memory_type.value, m.priority.value, content, tags)

    console.print(table)


@memory_group.command(name="search")
@click.argument("keyword")
def memory_search(keyword: str) -> None:
    """Search memories by keyword."""
    store = MemoryStore()
    results = store.search(keyword)

    if not results:
        console.print(f"[dim]No memories matching '{keyword}'[/dim]")
        return

    table = Table(title=f"Search: '{keyword}' ({len(results)} results)")
    table.add_column("ID", width=10)
    table.add_column("Type", width=10)
    table.add_column("Content", max_width=60)

    for m in results[:20]:
        content = m.content[:57] + "..." if len(m.content) > 60 else m.content
        table.add_row(m.id, m.memory_type.value, content)

    console.print(table)


@memory_group.command(name="add")
@click.argument("content")
@click.option(
    "--type",
    "memory_type",
    type=click.Choice([t.value for t in MemoryType]),
    default="lesson",
    help="Memory type.",
)
@click.option(
    "--priority",
    type=click.Choice([p.value for p in MemoryPriority]),
    default="medium",
    help="Priority.",
)
@click.option("--tag", multiple=True, help="Tags (repeatable).")
def memory_add(
    content: str,
    memory_type: str,
    priority: str,
    tag: tuple[str, ...],
) -> None:
    """Add a new memory."""
    store = MemoryStore()
    memory = store.add(
        content=content,
        memory_type=MemoryType(memory_type),
        priority=MemoryPriority(priority),
        tags=list(tag),
    )
    console.print(f"[green]Memory {memory.id} created[/green]")


@memory_group.command(name="digest")
def memory_digest() -> None:
    """Show digest of recent session memories."""
    store = MemoryStore()
    digest = store.create_digest(session_id="current")

    console.print(f"[bold]Session Digest[/bold] ({digest.count} memories)")
    for mtype in MemoryType:
        typed = digest.by_type(mtype)
        if typed:
            console.print(f"\n[bold]{mtype.value.upper()}[/bold] ({len(typed)})")
            for m in typed:
                console.print(f"  * {m.content[:80]}")


@memory_group.command(name="prune")
@click.option(
    "--days",
    default=30,
    help="Remove low-priority memories older than N days.",
)
def memory_prune(days: int) -> None:
    """Remove old low-priority memories."""
    store = MemoryStore()
    removed = store.prune(days=days)
    console.print(f"[green]Pruned {removed} memories[/green]")
