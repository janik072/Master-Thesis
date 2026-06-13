"""CLI entry point for the MAS framework."""
from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from dotenv import load_dotenv

load_dotenv()

app = typer.Typer(name="mas", help="Multi-Agent Stakeholder Simulation Framework")


@app.command()
def validate(
    scenario: Path = typer.Argument(..., help="Path to scenario.yaml"),
    personas: Path = typer.Argument(..., help="Path to personas/ directory"),
    run_config: Path = typer.Argument(..., help="Path to run_config.yaml"),
) -> None:
    """Validate input files against schemas without running a simulation."""
    from mas.engine.scenario_engine import build_resolved_scenario

    try:
        resolved = build_resolved_scenario(scenario, personas, run_config)
        typer.echo(f"✓ Scenario: {resolved.scenario.name}")
        typer.echo(f"✓ Agents:   {len(resolved.agents)}")
        for agent in resolved.agents:
            typer.echo(f"    - {agent.agent_id} ({agent.persona.label})")
        typer.echo(
            f"✓ Rounds:   {resolved.scenario.interaction.rounds.min}"
            f"–{resolved.scenario.interaction.rounds.max}"
        )
        typer.echo(f"✓ Budget:   ${resolved.run_config.cost.budget_total_usd}")
        typer.echo(f"✓ Model:    {resolved.run_config.llm.default_model}")
        typer.echo(f"✓ Hash:     {resolved.config_hash}")
        typer.echo("\nAll inputs valid. ✓")
    except Exception as e:
        typer.echo(f"✗ Validation error: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def run(
    scenario: Path = typer.Argument(..., help="Path to scenario.yaml"),
    personas: Path = typer.Argument(..., help="Path to personas/ directory"),
    run_config: Path = typer.Argument(..., help="Path to run_config.yaml"),
) -> None:
    """Run a simulation."""
    from mas.engine.orchestrator import run_simulation
    from mas.engine.scenario_engine import build_resolved_scenario

    resolved = build_resolved_scenario(scenario, personas, run_config)
    typer.echo(f"Starting simulation: {resolved.scenario.name}")
    typer.echo(f"  Agents: {len(resolved.agents)} | Rounds: {resolved.scenario.interaction.rounds.max}")
    typer.echo(f"  Model: {resolved.run_config.llm.default_model}")
    typer.echo(f"  Budget: ${resolved.run_config.cost.budget_total_usd}")
    typer.echo()

    output_dir = asyncio.run(run_simulation(resolved))
    typer.echo(f"\nSimulation complete.")
    typer.echo(f"Output: {output_dir}")


if __name__ == "__main__":
    app()
